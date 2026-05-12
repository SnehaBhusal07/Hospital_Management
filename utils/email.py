import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text      import MIMEText
from flask                import current_app


def send_booking_email(to_email, patient_name, doctor_name,
                       specialization, date, time_slot,
                       appointment_id):

    # email subject
    subject = 'Appointment Confirmation — MediPortal'

    # HTML email body
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background:#f4f9f9;
                 padding:20px;">

        <div style="max-width:600px; margin:0 auto;
                    background:white; border-radius:10px;
                    overflow:hidden;
                    box-shadow:0 2px 10px rgba(0,0,0,0.1);">

            <!-- Header -->
            <div style="background:#0F4C5C; padding:25px;
                        text-align:center;">
                <h1 style="color:white; margin:0;
                           font-size:24px;">MediPortal</h1>
                <p style="color:#a8d8e8; margin:5px 0 0;">
                    Hospital Appointment and Patient Management System
                </p>
            </div>

            <!-- Body -->
            <div style="padding:30px;">

                <h2 style="color:#0F4C5C;">
                     Appointment Confirmed!
                </h2>

                <p style="color:#555; font-size:15px;">
                    Dear <strong>{patient_name}</strong>,
                </p>
                <p style="color:#555; font-size:15px;">
                    Your appointment has been successfully booked.
                    Here are your booking details:
                </p>

                <!-- Ticket box -->
                <div style="background:#f0f9f6; border-radius:8px;
                            padding:20px; margin:20px 0;
                            border-left:4px solid #0F4C5C;">

                    <table style="width:100%; border-collapse:collapse;">
                        <tr>
                            <td style="padding:8px 0; color:#888;
                                       font-size:13px; width:40%;">
                                 Ticket ID
                            </td>
                            <td style="padding:8px 0; color:#333;
                                       font-weight:bold; font-size:13px;">
                                #APT-{appointment_id:04d}
                            </td>
                        </tr>
                        <tr>
                            <td style="padding:8px 0; color:#888;
                                       font-size:13px;">
                                 Patient Name
                            </td>
                            <td style="padding:8px 0; color:#333;
                                       font-size:13px;">
                                {patient_name}
                            </td>
                        </tr>
                        <tr>
                            <td style="padding:8px 0; color:#888;
                                       font-size:13px;">
                                 Doctor
                            </td>
                            <td style="padding:8px 0; color:#333;
                                       font-size:13px;">
                                {doctor_name}
                            </td>
                        </tr>
                        <tr>
                            <td style="padding:8px 0; color:#888;
                                       font-size:13px;">
                                 Specialization
                            </td>
                            <td style="padding:8px 0; color:#333;
                                       font-size:13px;">
                                {specialization}
                            </td>
                        </tr>
                        <tr>
                            <td style="padding:8px 0; color:#888;
                                       font-size:13px;">
                                 Date
                            </td>
                            <td style="padding:8px 0; color:#333;
                                       font-size:13px;">
                                {date}
                            </td>
                        </tr>
                        <tr>
                            <td style="padding:8px 0; color:#888;
                                       font-size:13px;">
                                 Time
                            </td>
                            <td style="padding:8px 0; color:#333;
                                       font-size:13px;">
                                {time_slot}
                            </td>
                        </tr>
                        <tr>
                            <td style="padding:8px 0; color:#888;
                                       font-size:13px;">
                                 Status
                            </td>
                            <td style="padding:8px 0;">
                                <span style="background:#d4f4e8;
                                             color:#0a6640;
                                             padding:3px 10px;
                                             border-radius:12px;
                                             font-size:12px;">
                                    Confirmed
                                </span>
                            </td>
                        </tr>
                    </table>

                </div>

                <p style="color:#555; font-size:14px;">
                    Please arrive <strong>10 minutes early</strong>
                    and bring this confirmation email.
                </p>

                <p style="color:#555; font-size:14px;">
                    To cancel or reschedule, please log in to
                    MediPortal or contact us.
                </p>

            </div>

            <!-- Footer -->
            <div style="background:#f9f9f9; padding:15px;
                        text-align:center; border-top:1px solid #eee;">
                <p style="color:#aaa; font-size:12px; margin:0;">
                    This is an automated email from MediPortal.
                    Please do not reply.
                </p>
            </div>

        </div>
    </body>
    </html>
    """

    try:
        # create email
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From']    = current_app.config['MAIL_FROM']
        msg['To']      = to_email

        # attach HTML
        msg.attach(MIMEText(html, 'html'))

        # connect to Gmail SMTP
        server = smtplib.SMTP(
            current_app.config['MAIL_SERVER'],
            current_app.config['MAIL_PORT']
        )
        server.ehlo()
        server.starttls()
        server.login(
            current_app.config['MAIL_USERNAME'],
            current_app.config['MAIL_PASSWORD']
        )
        server.sendmail(
            current_app.config['MAIL_FROM'],
            to_email,
            msg.as_string()
        )
        server.quit()

        return True

    except Exception as e:
        print('Email error:', e)
        return False