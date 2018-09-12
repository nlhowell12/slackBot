import unittest
import slackbot


class slackbotTest(unittest.TestCase):
    def test_handle(self):
        "Tests the handle command functions inputs"
        self.assertEqual(
            slackbot.handle_command('42', "channel"),
            "Life, the Universe, and Everything")
        self.assertIsNot(
            slackbot.handle_command('top10movies', "channel"),
            "Not sure what you mean. Try *{}*, *{}*, *{}*.".format(
                42, "top10movies", "worst10movies"))
        self.assertIsNot(
            slackbot.handle_command('worst10movies', "channel"),
            "Not sure what you mean. Try *{}*, *{}*, *{}*.".format(
                42, "top10movies", "worst10movies"))


if __name__ == '__main__':
    unittest.main()
