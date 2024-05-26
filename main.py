import json.decoder
import requests
global headers
from imapclient import IMAPClient
import yaml
import os
import email
from PIL import Image
import pytesseract

eventuseradmincookie = 'REDACTED'
ai_session = 'REDACTED'

headers = {
    "Cookie": f"ai_session={ai_session}; EventUserAdmin.Cookie={eventuseradmincookie}; .AspNetCore.Antiforgery.RtGCWVXC8-4=CfDJ8L_T8RCLIxpJpL6CgxrTkKF-z7bENb9GFEnpvne0VDtxgqURr3yftB79uNZ1Y96tm85XZQUwwZVmlVQnt-FmBgDaLb6VMd5IMZgVTu3HaBHkkVg7FuVKUNVbeGUKcB6-JAcn2IYWPbojc8I0aS7cx-Y; REDACTED",
    "request-id": "REDACTED",
    "x-csrf-token": "REDACTED",
    "traceparent": "REDACTED",
    "content-type": "application/json"
}

def getOrders(headers, eventID, orderStatus):
    data = '{"eventIds":null,"orderNo":null,"orderStatus":"' + orderStatus + '","orderType":null,"paymentTypes":["all"],"tickets":null,"orderedStartDate":null,"orderedEndDate":null,"customSearchFields":[],"sortField":"id","sortOrder":"desc","page":1,"pageSize":60000}'
    try:
        r = requests.post(f'https://appv3.eventnook.com/api/v1/order/list/{eventID}', data=data, headers=headers)
        r = r.json()
        if r["status"] == "success":
            print(r["data"]["orders"])
            return r["data"]["orders"]
        else:
            print(f"ERROR | {r.text}")
            return False
    except json.decoder.JSONDecodeError:
        print(f"ERROR | JSON Not Found/Could not be decoded - {r.text}")
        return False


def cancelOrder(headers, eventID, orderNo, orderID):

    data = '{"orderId":"' + f'{orderID}","orderNo":"{orderNo}","notesToBuyer":"","internalNotes":"","addCCEmails":false,"ccEmailList":""' +  '}'
    try:
        r = requests.post(f'https://appv3.eventnook.com/api/v1/order/cancel/{eventID}', data=data, headers=headers)
        r = r.json()
        if r["status"] == "success":
            return True
        else:
            print(f"ERROR |{r.text}")
            return False
    except json.decoder.JSONDecodeError:
        print(f"ERROR | JSON Not Found/Could not be decoded - {r.text}")
        return False

def getPendingOrders(headers, eventID):
    pendingOrders = getOrders(headers, eventID, "PENDING")
    if pendingOrders:
        return pendingOrders
    else:
        return None

def getConfirmedOrders(headers, eventID):
    confirmedOrders = getOrders(headers, eventID, "APPROVED")
    if confirmedOrders:
        return confirmedOrders
    else:
        return None

def getNonCancelledOrders(headers, eventID):
    # nonCancelledOrders = []

    pendingOrders = getPendingOrders(headers, eventID)
    # if pendingOrders:
    #     nonCancelledOrders.append(pendingOrders)

    confirmedOrders = getConfirmedOrders(headers, eventID)
    # if confirmedOrders:
    #     nonCancelledOrders.append(confirmedOrders)
    try:
        nonCancelledOrders = [*pendingOrders, *confirmedOrders]
    except TypeError:
        return confirmedOrders
    return nonCancelledOrders


def getOrderDetails(eventID, orderNo):
    all_orders = getOrders(headers, eventID, 'all')
    for order in all_orders:
        if order['orderNo'] == orderNo:
            return order


def getOrderItems(eventID, orderNos):
    track = {}
    for orderNo in orderNos:
        order = getOrderDetails(eventID, orderNo)
        uid = order["uid"]

        r = requests.get(f'https://appv3.eventnook.com/manage/order/vieworder/{eventID}/{uid}/{orderNo}', headers=headers)
        # print(r.text)
        # print(str(r.text.split('_ss.appData = ')[1]))
        items = []
        x = json.loads(r.text.split('_ss.appData = ')[1].split('};')[0] + '}')
        for item in x['order']['orderItems']:
            try:
                if track[item["itemName"]]:
                    track[item["itemName"]] += item["quantity"]
            except:
                track[item["itemName"]] = item["quantity"]
            # items.append(f'{item["itemName"]},{item["quantity"]}')
        print(track)
    return track


def approveOrder(headers, eventID, orderNo, orderID):

    data = '{"orderId":"' + str(orderID) + '","orderNo":"' + str(orderNo) + '","paymentReceivedDate":null,"chequeNo":"","internalNotes":""}'
    r = requests.post('https://appv3.eventnook.com/api/v1/order/approve/' + eventID, headers=headers, data=data)
    if r.json()['status'] == 'success':
        return True
    return False



def getEmailBody(msg):
    if msg.is_multipart():
        return getEmailBody(msg.get_payload(0))
    else:
        return msg.get_payload(None, True)


def getEmailAttachments(msg, reg_no):
    for part in msg.walk():
        if part.get_content_maintype() == 'multipart':
            continue
        if part.get('Content-Disposition') is None:
            continue

        file_name = reg_no + '.' + part.get_filename().rsplit('.', 1)[-1]  # Get the filename

        if bool(file_name):
            with open('attachments/' + file_name, 'wb') as f:
                f.write(part.get_payload(decode=True))
                return file_name
        return False


def connectGmail(email, password):
    HOST = 'imap.gmail.com'  # IMAP Host Server
    server = IMAPClient(HOST, use_uid=True, ssl=True)
    server.login(email, password)

    return server

def searchGmail_subject(server, mailbox, subject):
    server.select_folder(mailbox)
    messages_ids = server.search([u'SUBJECT', subject])
    messages_data = server.fetch(messages_ids, ['FLAGS', 'ENVELOPE', 'RFC822'])

    return messages_data

def searchGmail_gmailSearch(server, mailbox, search):
    server.select_folder(mailbox)
    messages_ids = server.gmail_search(search)
    messages_data = server.fetch(messages_ids, ['FLAGS', 'ENVELOPE', 'RFC822'])

    return messages_data

def checkEmailFreshness(server, msgid):
    gmail_labels = server.get_gmail_labels(msgid)[msgid]
    if 'Sweater Sales Apr 2023' in gmail_labels:
        return False
    return True

def ocrImage(filePath):
    image_file = Image.open(filePath)
    image_file = image_file.convert('L')  # convert image to black and white
    text = pytesseract.image_to_string(image_file, lang='eng', config='--psm 6')

    return text


while True:
    eventID = input("""
    Welcome to REN's Eventnook Panel!
    To proceed, enter the Event ID you'd like to work with.

    Event ID:  """)

    option = input(f"""
    Thanks! We're working with Event ID {eventID}. How can I help?
    [1] Get Orders
    [2] Cancel Orders
    [3] Validate Payments - OCR Auto
    [4] Validate Payments - Gmail Search (eg. Labels)
    Enter an option:
    """)

    if option == 1:
        option = input("""This option is currently in development!""")
    elif option == '2':
        option = input("""
        Sure! Which type of orders would you like to cancel?
        [1] All Orders
        [2] Confirmed Orders only
        [3] Pending Orders only

        Enter an option:
        """)
        if option == '1':
            nonCancelledOrders = getNonCancelledOrders(headers, eventID)
            nonCancelledCount = len(nonCancelledOrders)
            confirm = input(f""""
            {nonCancelledCount} Non Cancelled Orders have been Found.
            Confirm Cancel All? [Y/N]:
            """)
            if confirm == 'Y':
                count = 0
                for order in nonCancelledOrders:
                    count += 1
                    orderID = order["uid"]
                    orderNo = order["orderNo"]
                    cancelStatus = cancelOrder(headers, eventID, orderNo, orderID)
                    if cancelStatus:
                        print(f"[{str(count)}] SUCCESS | CANCELLED Order {orderNo} by {order['buyerFullName']}")
                    else:
                        print(f"[{str(count)}] ERROR | Order {orderNo} by {order['buyerFullName']}")
    elif option == '3':
        search_key = input("""
        Sure! Please provide a unique search key for this event's Payment Emails.
        We'll be checking REDACTED@gmail.com

        Search Key: """)
        #label:sweater-sales-apr-2023-to-be-checked REDACTED
        server = connectGmail('REDACTED', 'REDACTED')
        messages = searchGmail_gmailSearch(server, 'INBOX', search_key)
        for msgid, data in messages.items():
            server.remove_gmail_labels(msgid, 'Sweater Sales Apr 2023/TO BE CHECKED')
            # if not checkEmailFreshness(server, msgid):
            #     print(f"ALREADY CHECKED | {str(data[b'ENVELOPE'].subject.decode())}")
            #     continue

            server.add_gmail_labels(msgid, 'Sweater Sales Apr 2023')
            orderNo = str(data[b'ENVELOPE'].subject.decode()).split('(#')[1].split(')')[0]

            raw = email.message_from_bytes(data[b'RFC822'])
            fileName = getEmailAttachments(raw, orderNo)
            if not fileName:
                print(f"NO ATTACHMENTS | {str(data[b'ENVELOPE'].subject.decode())}")
                continue

            orderDetails = getOrderDetails(eventID, orderNo)
            try:
                if orderDetails['orderStatus'] == 'PENDING':
                    name = orderDetails['buyerFullName']
                    price = str(orderDetails['grandTotalAmount'])
                    # maybe do a check for just no decimal like '24' (ref: 724531272424EF02.jpg)
                    ocrText = str(ocrImage('attachments/' + str(fileName)))
                    if price in ocrText:
                        orderID = orderDetails['uid']
                        if not approveOrder(headers, eventID, orderNo, orderID):
                            input(f"ERROR | Could not approve {orderNo} by {name} for ${price}. Press key to continue")
                        else:
                            print(f'APPROVED | {orderNo} by {name} for ${price}')
                            server.add_gmail_labels(msgid, 'Sweater Sales Apr 2023/APPROVED')
                    else:
                        print(f'PENDING | {orderNo} by {name} for ${price}')
                        server.add_gmail_labels(msgid, 'Sweater Sales Apr 2023/PENDING')
                elif orderDetails['orderStatus'] == 'CANCELLED':
                    print(f'ORDER CANCELLED | {orderNo}')
            except Exception as e:
                print(f'UNKNOWN EXCEPTION CAUGHT | {orderNo}')
                input(e)
    elif option == '4': #this is pre-set in some ways to the shirt sale, and is not 100% modular yet.
        search_key = input("""
        Sure! Please provide a Gmail Search Key for this event's Payment Emails.
        We'll be checking REDACTED@gmail.com

        Gmail Search Key: """)

        server = connectGmail('REDACTED', 'REDACTED')
        messages = searchGmail_gmailSearch(server, 'INBOX', search_key)
        for msgid, data in messages.items():
            orderNo = str(data[b'ENVELOPE'].subject.decode()).split('(#')[1].split(')')[0]

            orderDetails = getOrderDetails(eventID, orderNo)
            try:
                if orderDetails['orderStatus'] == 'PENDING':
                    name = orderDetails['buyerFullName']
                    price = str(orderDetails['grandTotalAmount'])
                    orderID = orderDetails['uid']
                    if not approveOrder(headers, eventID, orderNo, orderID):
                        input(f"ERROR | Could not approve {orderNo} by {name} for ${price}. Press key to continue")
                    else:
                        print(f'APPROVED | {orderNo} by {name} for ${price}')
                        server.add_gmail_labels(msgid, 'Sweater Sales Apr 2023/APPROVED')
                        server.remove_gmail_labels(msgid, 'Merch Sales Nov 2022/MANUAL')
                elif orderDetails['orderStatus'] == 'CANCELLED':
                    print(f'ORDER CANCELLED | {orderNo}')
            except Exception as e:
                print(f'UNKNOWN EXCEPTION CAUGHT | {orderNo}')
                input(e)
