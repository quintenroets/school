import json

from .sessionmanager import SessionManager
from libs.parser import Parser


class ZoomApi:
    tokens = {}

    def get_content(course_id):
        form_url = f"https://ufora.ugent.be/d2l/lms/remoteplugins/lti/launchLti.d2l?ou={course_id}" \
                   f"&pluginId=556e197e-e87b-4c27-be5d-53adc7a41826&d2l_body_type=3"
        form = SessionManager.get(form_url).content
        post_content, _ = SessionManager.post_form(form)

        if b"errorCode" in post_content:
            content = json.dumps({"result": {"list": []}}).encode()
        else:
            info_items = ["ssidToken", "oauthConsumerKey", "scid"]
            info = {k: Parser.between(post_content, f'{k}:"'.encode(), '"'.encode()).decode() for k in info_items}
            info["X-XSRF-TOKEN"] = Parser.between(post_content, b'X-XSRF-TOKEN", value:"', b'"').decode()

            headers = {
                "X-XSRF-TOKEN": info["X-XSRF-TOKEN"],
                "referer": f"https://applications.zoom.us/lti/rich?lti_scid={info['scid']}&oauth_consumer_key={info['oauthConsumerKey']}"
            }
            api_url = f"https://applications.zoom.us/api/v1/lti/rich/recording/COURSE?startTime=&endTime=&keyWord=&searchType=1" \
                      f"&status=&page=1&total=0&lti_scid={info['scid']}"
            r = SessionManager.get(api_url, headers=headers)
            info["headers"] = r.request.headers
            ZoomApi.tokens[course_id] = info
            content = r.content

        return content
