import unittest
from unittest.mock import patch
import subscription_builder as sb


class SubscriptionBuilderTests(unittest.TestCase):
    def test_anycast_excluded(self):
        self.assertFalse(sb.matches_country("trojan://pw@host.test:443#🇩🇪 Anycast", {"germany"}))

    def test_country_and_validation(self):
        node = "vless://uuid@host.test:443?security=tls#🇫🇮 Finland"
        self.assertTrue(sb.valid_node(node))
        self.assertTrue(sb.matches_country(node, {"finland"}))
        self.assertFalse(sb.matches_country(node, {"germany"}))

    def test_distinct_transport_not_deduplicated(self):
        a = "vless://uuid@host.test:443?type=ws#🇩🇪 Germany"
        b = "vless://uuid@host.test:443?type=grpc#🇩🇪 Germany"
        self.assertNotEqual(sb.identity(a), sb.identity(b))
        self.assertEqual(sb.identity(a), sb.identity(a.split("#")[0] + "#other"))

    def test_invalid_nodes(self):
        for node in ["hello", "vless://", "trojan://pw@host.test", "http://x:y@host.test:443"]:
            self.assertFalse(sb.valid_node(node))


if __name__ == "__main__":
    unittest.main()
