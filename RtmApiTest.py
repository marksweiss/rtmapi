import unittest
import RtmApi

class RtmApiTestCase(unittest.TestCase):
    def setUp(self):
        # This account is closed so these keys don't mean anything
        self.api_key = '73a99620f6bacb82f2d8eeefcfd3994d'
        self.shared_secret = '3711530aee2dc566'
        self.rtm = RtmApi.RtmApiLib(self.api_key, self.shared_secret)
    
    # def tearDown(self):
    
    #def testInit(self):
    #    self.assertEqual(self.rtm.RTM_API_BASE_METH_URL, 'http://www.rememberthemilk.com/services/rest/?')
    #    self.assertEqual(self.rtm.API_KEY, self.api_key)
    #    print "\n"

    #def test_loadFrob_callRtmApiMethod_signParams(self):
    #    frob = self.rtm.loadFrob()
    #    self.assertTrue(len(frob) > 0)
    #    print "\nFrob = " + frob + "\n"
        
    #def testLoadAuthToken(self):
    #    authToken = self.rtm.loadAuthToken()
    #    self.assertTrue(len(authToken) > 0)
    #    print "\nAuthToken = " + authToken + "\n"

    #def testGetRtmTasksXml(self):
    #    tasks = self.rtm.getRtmTasksXml()
    #    self.assertTrue(len(tasks) > 0)
    #    print "\nTasks = " + tasks + "\n"

    def testGetRtmTasksByTag(self):
		tags = self.rtm.getRtmTasksByTag()
		# self.assertTrue(len(tags) > 0)
		for tag in tags:
			print tag