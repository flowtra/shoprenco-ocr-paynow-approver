# Shopren.co Paynow QR OCR Checker
## PROBLEM
My club’s social enterprise collected order payments via paynow, and these transactions could only be verified via screenshots as the school did not approve of payment processors such as Stripe/Hitpay etc. Normally, these screenshots would have to be checked one-by-one against the order number in Eventnook, and then manually approved.

## SOLUTION
Having about 875 orders/screenshots to check, I knew there was a more efficient way of doing things. I thus used IMAP to login to our Gmail account which receives all the screenshots, and employed OCR to verify that the screenshots contained the accurate payment amount. By parsing the order number from the email’s subject, the program then automatically approves the order via a POST request sent to Eventnook’s API, which was also reverse engineered.

## IMPACT
This program saved hours of time and allowed my team to handle other more urgent issues. When the program first ran, it cleared the backlog of 875 screenshots within an hour, and then ran 24/7 to automatically approve more PayNow screenshots coming in live.
