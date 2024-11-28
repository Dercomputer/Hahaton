import xml.etree.ElementTree as ET

class OfferParser:
    def __init__(self, xml_file):
        self.tree = ET.parse(xml_file)
        self.root = self.tree.getroot()

    def parse_offers(self):
        offers = self.root.find('shop').find('offers')
        result = []
        for offer in offers:
            offer_data = [
                offer.find('price').text,
                offer.find('currencyId').text,
                offer.find('picture').text,
                offer.find('name').text,
                offer.find('vendor').text,
                offer.find('description').text,
                offer.find('barcode').text
            ]
            for param in offer.findall('param'):
                offer_data.append(param.text)
            result.append(offer_data)
        return result

# Пример использования
if __name__ == "__main__":
    parser = OfferParser('yandex_feed.xml')
    offers_data = parser.parse_offers()
    a = 0
    for offer in offers_data:
        print(offer)
        a += 1
    print(a)