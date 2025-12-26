from flask import Flask, render_template, request, jsonify
import imaplib
import smtplib
import email
from email.header import decode_header
from email.mime.text import MIMEText

IMAP_HOST = "imap.gmail.com"
SMTP_HOST = "smtp.gmail.com"
IMAP_PORT = 993
SMTP_PORT = 587

EMAIL_ACCOUNT = "thongbaokh@vimo.vn"
EMAIL_PASSWORD = "jelh lqgh gfrm xzyh"

app = Flask(__name__)

# ========== IMAP SEARCH ==========
def search_inbox_by_merchant(merchant_email):
    mail = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
    mail.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
    mail.select("INBOX")

    status, data = mail.search(
        None,
        f'(OR FROM "{merchant_email}" TO "{merchant_email}")'
    )

    email_ids = data[0].split()
    results = []

    for eid in email_ids:
        _, msg_data = mail.fetch(eid, "(RFC822)")
        msg = email.message_from_bytes(msg_data[0][1])

        subject, encoding = decode_header(msg["Subject"])[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding or "utf-8", errors="ignore")

        results.append({
            "id": eid.decode(),
            "subject": subject,
            "from": msg.get("From"),
            "date": msg.get("Date")
        })

    mail.logout()
    return results


def get_email_body_by_id(email_id):
    mail = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
    mail.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
    mail.select("INBOX")

    _, msg_data = mail.fetch(email_id.encode(), "(RFC822)")
    msg = email.message_from_bytes(msg_data[0][1])

    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
    else:
        body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")

    mail.logout()
    return msg["Subject"], body


def resend_email(subject, body, merchant_email):
    msg = MIMEText(body, "html", "utf-8")
    msg["Subject"] = subject
    msg["From"] = EMAIL_ACCOUNT
    msg["To"] = merchant_email

    server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
    server.starttls()
    server.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
    server.send_message(msg)
    server.quit()


# ========== ROUTES ==========
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/search", methods=["POST"])
def search():
    merchant_email = request.json["merchant_email"]
    emails = search_inbox_by_merchant(merchant_email)
    return jsonify(emails)


@app.route("/resend", methods=["POST"])
def resend():
    email_id = request.json["email_id"]
    merchant_email = request.json["merchant_email"]

    subject, body = get_email_body_by_id(email_id)
    resend_email(subject, body, merchant_email)

    return jsonify({"status": "success"})


# if __name__ == "__main__":
#     app.run(debug=True)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
