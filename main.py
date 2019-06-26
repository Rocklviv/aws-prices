__name__ = "AWSPrices"
from flask import Flask, jsonify
from flask_cors import CORS
from flask_restful import Api
from libs.gzip import gzipped


application = Flask(__name__)
api = Api(application)
cors = CORS(application, origins="*")

# Application related imports
from controllers.aws_prices import AWSPrices
from controllers.health import HealthPage
aws_prices = AWSPrices()


@application.route('/prices', methods=['GET'])
@gzipped
def get_prices():
    try:
        return jsonify(aws_prices.get_prices())
    except ImportError as exc:
        raise exc.msg

@application.route('/health', methods=['GET', 'POST'])
def health_check():
    return HealthPage.check()

if __name__ == "AWSPrices":
    application.run(
        host="0.0.0.0",
        port=8080,
        threaded=True
    )