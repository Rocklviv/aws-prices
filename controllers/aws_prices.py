import os
import json
import requests
from libs.cache import CacheController, CachedObject


class AWSPrices:
    """
    TODO: Improve class to use a versioned data instead of current, so that we will be able
    to have only on data file instead of daily data stored on the disk.
    https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEC2/20180628005902/us-west-1/index.json
    """
    # AWS Pricing API Base url
    AWS_PRICE_BASE_URL = "https://pricing.us-east-1.amazonaws.com"
    # AWS All pricing for different offers.
    AWS_ALL_OFFERS = "/offers/v1.0/aws/index.json"
    # AWS Pricing EC2 Region indexes
    AWS_REGION_OFFERS = "/offers/v1.0/aws/AmazonEC2/current/region_index.json"
    # AWS Pricing offer key
    AWS_OFFERS_KEY = "currentVersionUrl"
    # HOURLY TERMS CODE
    AWS_HOURLY_TERMS_CODE = "JRTCKXETXF"
    # AWS RATES CODE
    AWS_RATE_CODE = "6YS6EN2CT7"
    #
    AWS_DEFAULT_TERMS = "OnDemand"

    def __init__(self):
        self.region = os.getenv("AWS_REGION") or "eu-west-1"
        self.home_dir = os.getenv("HOME") or "/tmp"
        self.products = []
        self.prices = []
        self.cache = CacheController(housekeeping=60)

    def get_prices(self, **kwargs):
        """

        :return:
        """
        if not self.cache.get('current_prices'):
            prices = self._get_offers()
            if prices:
                prices_obj = CachedObject('current_prices', json.loads(prices), ttl=3600)
                self.cache.add(obj=prices_obj)

        if not self.cache.get('generated_prices'):
            list_prices = self._generate(self._read_prices(self.cache.get('current_prices')))
            generated_obj = CachedObject('generated_prices', list_prices, ttl=3600)
            self.cache.add(generated_obj)
        return self.cache.get('generated_prices')

    def _get_version(self):
        """

        :return:
        """
        try:
            version_response = requests.get('{base_url}{version}'.format(
                base_url=self.AWS_PRICE_BASE_URL, version=self.AWS_ALL_OFFERS))
            if version_response.status_code == 200:
                response = json.loads(version_response)
                if response and response.get('publicationDate'):
                    version_cache = CachedObject('version', response.get('publicationDate'),
                                                 ttl=604800)
                    if self.cache.get('version'):
                        if self.cache.get('version') == response.get('publicationDate'):
                            return self.cache.get('version')
                        else:
                            self.cache.add(version_cache)
                    else:
                        self.cache.add(version_cache)
            return self.cache.get('version')
        except requests.ConnectionError as exp:
            print(exp)
            exit(1)

    def _read_prices(self, prices):
        """
        Reads JSON response and generates by short SKU based list of prices.
        :param prices: JSON|string
        :return: list
        """
        data = prices
        list_prices = []
        for k, v in data.get('products').items():
            if v.get('attributes').get('currentGeneration') == 'Yes':
                self.products.append({k: {"instance_type": v.get("attributes").
                                 get("instanceType"), "storage": v.get("attributes").get(
                    "storage")}})

        for sku_id, hourly_price in data.get('terms').get(self.AWS_DEFAULT_TERMS).items():
            for hourly_price_id, price_rates in data.get('terms').get(self.AWS_DEFAULT_TERMS).get(
                    sku_id).items():
                rates = "{}.{}.{}".format(sku_id, self.AWS_HOURLY_TERMS_CODE, self.AWS_RATE_CODE)
                if "{}.{}".format(sku_id, self.AWS_HOURLY_TERMS_CODE):
                    if sku_id == price_rates.get('sku'):
                        if rates in price_rates.get('priceDimensions'):
                            list_prices.append({"sku": sku_id,
                                            "price": price_rates.get('priceDimensions').get(
                                                rates).get('pricePerUnit').get('USD')})

        return list_prices

    def _get_offers(self):
        """
        Gets EC2 offers and returns dict with prices.
        :return: dict|boolean
        """
        try:
            offers = requests.get("{base_url}{offers}".format(base_url=self.AWS_PRICE_BASE_URL,
                                                             offers=self.AWS_REGION_OFFERS))

            if offers.status_code == 200:
                response = json.loads(offers.text)
                regions = response.get('regions')
                if regions:
                    offer = regions.get(self.region).get(self.AWS_OFFERS_KEY)
                    offers_url = "{base_url}{offer}".format(base_url=self.AWS_PRICE_BASE_URL,
                                                             offer=offer)
                    data = requests.get(offers_url)
                    if data.status_code == 200:
                        return data.text
                    else:
                        return json.dumps(dict())
            return False
        except requests.ConnectionError as exp:
            print(exp)
            exit(1)

    def _generate(self, prices):
        """
        Combines prices and instance to one list of objects.
        :param prices: array|list SKU Short list of prices.
        :return: list
        """
        for i in self.products:
            for i2 in prices:
                for sku_id, obj in i.items():
                    if sku_id in i2.get('sku'):
                        self.prices.append({"sku": sku_id, "price": i2.get('price'),
                                            "instance_type": obj.get('instance_type'),
                                            "storage": obj.get('storage')})
        return self.prices
