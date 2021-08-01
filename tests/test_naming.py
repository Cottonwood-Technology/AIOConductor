from aioconductor.naming import camelcase_to_underscore


def test_camelcase_to_underscore() -> None:
    assert camelcase_to_underscore("DB") == "db"
    assert camelcase_to_underscore("HTTPClient") == "http_client"
    assert camelcase_to_underscore("CoolXMLParser") == "cool_xml_parser"
    assert camelcase_to_underscore("MessageQueue") == "message_queue"
    assert camelcase_to_underscore("RSA512Crypt") == "rsa_512_crypt"
