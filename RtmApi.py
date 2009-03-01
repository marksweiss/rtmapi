"""RtmApi: Python binding for RememberTheMilk.com REST API."""

__version__ = "0.1"
__author__ = "mark_s_weiss"
__credits__ = "Portions adapted from pyrtm by ykabhinav, (C) 2007 ykabhinav"
__copyright__ = "(C) 2007 mark_s_weiss."


import md5
import urllib
import webbrowser
from xml.dom import minidom, Node
import time
import sys


class RtmApiLib:
        
    # Some RTM API constants
    RTM_API_BASE_METH_URL = 'http://www.rememberthemilk.com/services/rest/?'
    RTM_API_BASE_AUTH_URL = 'http://www.rememberthemilk.com/services/auth/?'
    RTM_API_PERMS = ('read', 'write', 'delete')
    RTM_API_PERMS_READ = RTM_API_PERMS[0]
    RTM_API_PERMS_WRITE = RTM_API_PERMS[1]
    RTM_API_PERMS_DELETE = RTM_API_PERMS[2]
    RTM_API_MIN_SECS_INTERVAL_BETW_CALLS = 1

    def __init__(self, api_key, shared_secret):
        '''Ctor for RtmApi object
           Args:
           api_key - RTM API key required for authenticated requests. Must be passed as value for api_key param, api_key = "1234"
           shared_secret - Additional RTM key. Used to create hashed digest of API call params, which itself becomes the value of additional param api_sig on authenticated requests.'''

        self.API_KEY = api_key
        self.SHARED_SECRET = shared_secret
        self.frob = ''
        self.auth_token = ''
    
    
    # Wrapper API methods
    def getRtmTasksXml(self):
        '''Retrieves the complete list of RTM Tasks for the session's authenticated user, in the XML document form defined by the RTM API.'''

        if self.auth_token == '':
            self.loadAuthToken()
        
        method = 'rtm.tasks.getList'
        params = {}
        return self.callRtmApiMethod(method, params)
            
    def getRtmTasksByTag(self):
        '''Retrieves the complete list of RTM Tasks for the session's authenticated user, grouped by the user's Tags. 
           Tasks appear under each Tag they are associated with.
           Tasks are returned as a Dictionary, with Tags as keys and Lists of Tasks (loaded into Python objects) as values.
           NOTE: call getRtmTasksXml() to get the XML representation of the Tasks as returned by the RTM API'''
        
        api_meth_ret = self.getRtmTasksXml()     
        dom = minidom.parseString(api_meth_ret)
        
        # Iterate all the Tasks and put them into a dictionary keyed to each tag; so each Task is mapped to each tag it has
        # This is obviously not as 'nice' as a 'real' xsl to do the transformation.
        tasksByTag = {}
        task_nodes = dom.getElementsByTagName('tasks')    # Oddly enough, this is the parent of a "Task" node in the RTM API XML return of getTasks()
        
        for task_node in task_nodes:                    
            task_node_lists = task_node.getElementsByTagName('list')                   
            for task_node_list in task_node_lists:
                list_id = task_node_list.attributes['id'].value
                task_series_nodes = task_node_list.getElementsByTagName('taskseries')                                
                if task_series_nodes:
                    for task_series_node in task_series_nodes:
                        # Get 'task' child, 'completed' attribute, if yes then don't include task
                        task_node = task_series_node.getElementsByTagName('task')[0]
                        
                        # Filter out completed tasks
                        is_completed = len(task_node.attributes['completed'].value) > 0
                        if not is_completed:
                            task_name = task_series_node.attributes['name'].value
                            
                            tags_node = task_series_node.getElementsByTagName('tags')
                            if tags_node:
                                tag_nodes = tags_node[0].getElementsByTagName('tag')                    
                                for tag_node in tag_nodes:
                                                                    
                                    tag = tag_node.firstChild.nodeValue
                                    task_tag_link = '<a href="' + self.buildRtmApiMethodCall('rtm.tasks.getList', {'list_id':list_id}) + '">' + task_name + '</a>'
                                    if tasksByTag.has_key(tag):
                                        tasksByTag[tag].append(task_tag_link) # task_node.toxml('utf-8') 
                                    else:
                                        tasksByTag[tag] = [task_tag_link] # task_node.toxml('utf-8')                        
        return tasksByTag
    # /Wrapper API methods
    
    
    # Helper operations        
    def loadFrob(self):
        '''Helper that retrieves a frob, which is a session key for an authenticated session of access to the RTM data of a user with a particular api_key.'''

        # Set the RTM API method to call, and init empty params
        method = 'rtm.auth.getFrob'
        params = {}
        # Make the call
        api_meth_ret = self.callRtmApiMethod(method, params)
        # Parse frob from result
        dom = minidom.parseString(api_meth_ret)
        self.frob = dom.getElementsByTagName('frob')[0].childNodes[0].data
        
        return self.frob
    
    def loadAuthToken(self, perms = 'read', auth_sleep_time = RTM_API_MIN_SECS_INTERVAL_BETW_CALLS):
        '''Helper that retrieves an authorization token.  Almost all API calls must pass this as an argument.
           Args:
           perms - read, write, delete; permissions for this session associated with the auth token being generated
           auth_sleep_time - how long to pause while the user authorizes the session on the RTM web site'''
        
        # Get a frob from RTM API
        self.loadFrob()
        
        # Set params for first auth call, launches an auth page for this user, they have to click button to allow this process to access their account
        params = {}
        params['api_key'] = self.API_KEY
        params['frob'] = self.frob
        params['perms'] = perms
        params['api_sig'] = self.signParams(params)        
        # Launch RTM API authorization page, with params:
        # api_key - key of account being authorized
        # frob - session key for current session
        # perms - read, write, delete; permissions for this session associated with the auth token being generated
        # api_sig - hash of the params, passed with all authenticated calls to the API
        api_meth_url = self.RTM_API_BASE_AUTH_URL + urllib.urlencode(params)        
        webbrowser.open_new(api_meth_url)
        time.sleep(auth_sleep_time)

        # Get the authorization token
        method = 'rtm.auth.getToken'
        params = {}
        params['frob'] = self.frob
        api_meth_ret = self.callRtmApiMethod(method, params)
        dom = minidom.parseString(api_meth_ret)
        self.auth_token = dom.getElementsByTagName('token')[0].childNodes[0].data

        return self.auth_token        

    # Method call helper
    def signParams(self, params):
        '''All authenticated API calls must include an argument which is the hash of the other parameters.
           Algorithm for signing parameters documented here:
             http://www.rememberthemilk.com/services/api/authentication.rtm
           Args:
           params - all the parameters, as name/value pairs in a hash, that are to be sent as arguments to an RTM API method call'''

        # API requires hash of params sorted ascending by key name
        keys = params.keys()
        keys.sort()
        # API requires prepending the shared_secrect to the sorted name value pairs concatenated, like so:  shared_secret + MD5Hash(SortedName1Value1SortedName2Value2 ...)
        api_sig = self.SHARED_SECRET
        for key in keys:
            api_sig += key + params[key]

        return md5.new(api_sig).hexdigest()
    # /Helper operations for authentication
                            
    # Helper because we want to get the call as a string to generate html file, and to use it to make in-memory calls
    def buildRtmApiMethodCall(self, method, params):
        '''Builds URL to call the api method from RTM
           Args:
           method - the api method we are calling.
           params - the params that we are sending for the method.'''
           
        # Add the required params for each call
        params['api_key'] = self.API_KEY
        params['method'] = method
        if self.auth_token is not '':
            params['auth_token'] = self.auth_token
        # Add the required param that is the hash of the other params
        params['api_sig'] = self.signParams(params)
        return self.RTM_API_BASE_METH_URL + urllib.urlencode(params)

    # Generic RTM API method call wrapper
    def callRtmApiMethod(self, method, params):
        '''Makes a request for the api method from RTM. Also puts a
           one second delay between calls, which is the current requirement for usage of the API
           Args:
           method - the api method we are calling.
           params - the params that we are sending for the method.'''
        
        # Force sleep of at least 1 second since last call before making this call. This is current requirement for usage of the API.
        time.sleep(self.RTM_API_MIN_SECS_INTERVAL_BETW_CALLS)
        
        api_meth_url = self.buildRtmApiMethodCall(method, params)
        return urllib.urlopen(api_meth_url).read()



# Some test code
print '<html><head></head><body>'

# This account is closed, so these keys don't matter
api_key = '73a99620f6bacb82f2d8eeefcfd3994d'
shared_secret = '3711530aee2dc566'
rtm = RtmApiLib(api_key, shared_secret)

tasksByTag = rtm.getRtmTasksByTag()
for k, v in tasksByTag.iteritems():
    print '<br/><b>Tag</b>: ' + k + '<br/>----------------------------------<br/>\n'
    for task in v:
        print task + '<br/>\n'

print '</body></html>'
