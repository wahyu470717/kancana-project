import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

def _send_email_via_resend(
    to_email: str,
    subject: str,
    html_content: str,
    cc_emails: list = None
):

    try:
        sender_email = f"{settings.MAIL_FROM_NAME} <{settings.MAIL_FROM_ADDRESS}>"
        
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = sender_email
        message["To"] = to_email
        
        if cc_emails:
            message["Cc"] = ", ".join(cc_emails)
        
        part = MIMEText(html_content, "html")
        message.attach(part)
        
        with smtplib.SMTP_SSL(settings.MAIL_HOST, settings.MAIL_PORT) as server:
            server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
            
            recipients = [to_email]
            if cc_emails:
                recipients.extend(cc_emails)
            
            server.sendmail(sender_email, recipients, message.as_string())
        
        logger.info(f" Email berhasil terkirim ke {to_email}")
        return True
          
    except Exception as e:
        logger.error(f"Gagal mengirim email ke {to_email}: {str(e)}")
        raise Exception(f"Gagal mengirim email: {str(e)}")


def send_admin_notification_new_registration(user_data: dict):

    try:
        subject = f"{settings.MAIL_FROM_NAME} - Registrasi User"
        
        html = f"""
        <html>
          <body style="font-family: Arial, sans-serif; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #f9f9f9; padding: 30px; border-radius: 10px;">
              <h2 style="color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px;">
                📋 Registrasi User Baru
              </h2>
              
              <p style="color: #666; margin-top: 20px;">
                Ada user baru yang melakukan registrasi dan menunggu verifikasi.
              </p>
              
              <div style="background-color: white; padding: 20px; border-radius: 8px; margin-top: 20px;">
                <h3 style="color: #333; margin-top: 0;">Data User:</h3>
                
                <table style="width: 100%; border-collapse: collapse;">
                  <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #eee; font-weight: bold; width: 40%;">NIP</td>
                    <td style="padding: 8px; border-bottom: 1px solid #eee;">{user_data.get('nip', '-')}</td>
                  </tr>
                  <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #eee; font-weight: bold;">Username</td>
                    <td style="padding: 8px; border-bottom: 1px solid #eee;">{user_data.get('username', '-')}</td>
                  </tr>
                  <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #eee; font-weight: bold;">Email</td>
                    <td style="padding: 8px; border-bottom: 1px solid #eee;">{user_data.get('email', '-')}</td>
                  </tr>
                  <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #eee; font-weight: bold;">Nama Lengkap</td>
                    <td style="padding: 8px; border-bottom: 1px solid #eee;">{user_data.get('full_name', '-')}</td>
                  </tr>
                  <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #eee; font-weight: bold;">Jabatan</td>
                    <td style="padding: 8px; border-bottom: 1px solid #eee;">{user_data.get('jabatan', '-')}</td>
                  </tr>
                  <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #eee; font-weight: bold;">Instansi</td>
                    <td style="padding: 8px; border-bottom: 1px solid #eee;">{user_data.get('organization', '-')}</td>
                  </tr>
                  <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #eee; font-weight: bold;">No. Telepon</td>
                    <td style="padding: 8px; border-bottom: 1px solid #eee;">{user_data.get('no_telepon', '-')}</td>
                  </tr>
                  <tr>
                    <td style="padding: 8px; font-weight: bold;">Waktu Registrasi</td>
                    <td style="padding: 8px;">{user_data.get('created_at', '-')}</td>
                  </tr>
                </table>
              </div>
              
              <div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; margin-top: 20px;">
                <p style="margin: 0; color: #856404;">
                  ⏳ <strong>Status:</strong> Menunggu Verifikasi Administrator
                </p>
              </div>
              
              <p style="color: #999; font-size: 12px; margin-top: 30px;">
                Email ini dikirim otomatis dari sistem {settings.MAIL_FROM_NAME}.<br>
                Silakan login ke dashboard admin untuk melakukan verifikasi.
              </p>
            </div>
          </body>
        </html>
        """
        
        return _send_email_via_resend(
            to_email=settings.ADMIN_NOTIFICATION_EMAIL,
            subject=subject,
            html_content=html
        )
          
    except Exception as e:
        logger.error(f"Gagal mengirim notifikasi admin: {str(e)}")
        return False


def send_reset_password_email(
    email: str, 
    reset_token: str,
    expires_at: datetime = None,
    user_display_name: str = None
):
    try:
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
        
        expires_display = ""
        if expires_at:
            expires_display = f"<p style='color: #999; font-size: 12px; margin-top: 30px;'>Link ini akan kadaluarsa pada {expires_at.strftime('%Y-%m-%d %H:%M %Z')}.<br>"
        else:
            expires_display = "<p style='color: #999; font-size: 12px; margin-top: 30px;'>Link ini akan kadaluarsa dalam 1 jam.<br>"
            
        greeting = f"Halo {user_display_name}," if user_display_name else "Halo,"
        
        subject = f"{settings.MAIL_FROM_NAME} - Reset Password"
        
        html = f"""
        <html>
          <body style="font-family: Arial, sans-serif; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #f9f9f9; padding: 30px; border-radius: 10px;">
              <h2 style="color: #333;">Reset Password</h2>
              <p>{greeting}</p>
              <p>Anda menerima email ini karena ada permintaan untuk reset password akun Anda.</p>
              <p>Klik tombol di bawah ini untuk reset password Anda:</p>
              <div style="text-align: center; margin: 30px 0;">
                <a href="{reset_url}" 
                    style="background-color: #4CAF50; color: white; padding: 12px 30px; 
                          text-decoration: none; border-radius: 5px; display: inline-block;">
                  Reset Password
                </a>
              </div>
              <p>Atau copy link berikut ke browser Anda:</p>
              <p style="word-break: break-all; color: #666;">{reset_url}</p>
              {expires_display}
              Jika Anda tidak meminta reset password, abaikan email ini.
              </p>
            </div>
          </body>
        </html>
        """
        
        return _send_email_via_resend(email, subject, html)
          
    except Exception as e:
        raise Exception(f"Gagal mengirim email: {str(e)}")

  
def send_registration_confirmation_email(email: str, user_display_name: str = None):
    try:
        greeting = f"Halo {user_display_name}," if user_display_name else "Halo,"
        
        subject = f"{settings.MAIL_FROM_NAME} - Konfirmasi Registrasi"
        
        html = f"""
        <html>
          <body style="font-family: Arial, sans-serif; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #f9f9f9; padding: 30px; border-radius: 10px;">
              <h2 style="color: #333;">Registrasi Berhasil</h2>
              <p>{greeting}</p>
              <p>Terima kasih telah melakukan registrasi di sistem {settings.MAIL_FROM_NAME}.</p>
              
              <div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <p style="margin: 0; color: #856404;">
                  ⏳ <strong>Status:</strong> Menunggu Verifikasi Administrator
                </p>
              </div>
              
              <p>Akun Anda sedang dalam proses verifikasi oleh administrator. Anda akan menerima email notifikasi untuk membuat password setelah akun Anda disetujui.</p>
              
              <p style="color: #999; font-size: 12px; margin-top: 30px;">
                Proses verifikasi biasanya memakan waktu 1-2 hari kerja.<br>
                Jika Anda tidak melakukan registrasi, abaikan email ini.
              </p>
            </div>
          </body>
        </html>
        """
        
        return _send_email_via_resend(email, subject, html)
          
    except Exception as e:
        logger.error(f"Failed to send registration confirmation email to {email}: {str(e)}")
        return False


def send_set_password_email(email: str, set_password_token: str, user_display_name: str = None):
    try:
        set_password_url = f"{settings.FRONTEND_URL}/set-password?token={set_password_token}"
        
        greeting = f"Bapak/Ibu {user_display_name}" if user_display_name else "Bapak/Ibu"
        
        subject = "Status Verifikasi Akun Dashboard Infrastruktur Jalan"
        
        html = f"""
        <html>
          <body style="font-family: Arial, sans-serif; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 30px; border-radius: 10px;">
              <p style="color: #333; margin-bottom: 20px;">Yang Terhormat {greeting},</p>
              
              <p style="color: #333; margin-bottom: 20px;">
                <strong>Selamat!</strong> Permohonan akun Anda pada <strong>KANCANA Dashboard Analitik Infrastruktur Jalan</strong> diterima.
              </p>
              
              <p style="color: #333; margin-bottom: 30px;">
                Silakan klik tombol berikut untuk membuat kata sandi.
              </p>
              
              <div style="text-align: center; margin: 30px 0;">
                <a href="{set_password_url}" 
                    style="background-color: #4CAF50; color: white; padding: 14px 40px; 
                          text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                  Buat Kata Sandi
                </a>
              </div>
              
              <p style="color: #666; font-size: 13px; margin-top: 20px;">
                Atau copy link berikut ke browser Anda:<br>
                <span style="word-break: break-all; color: #4CAF50;">{set_password_url}</span>
              </p>
              
              <p style="color: #333; margin-top: 30px;">
                Terima kasih atas perhatian dan kerjasama Bapak/Ibu.
              </p>
              
              <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee;">
                <p style="color: #333; margin: 5px 0;">Hormat kami,</p>
                <p style="color: #333; margin: 5px 0; font-weight: bold;">Tim KANCANA</p>
                <p style="color: #666; margin: 5px 0; font-size: 13px;">Dashboard Analitik Infrastruktur Jalan</p>
              </div>
              
              <p style="color: #999; font-size: 11px; margin-top: 30px; text-align: center;">
                Link ini akan kadaluarsa dalam 24 jam.<br>
                Email ini dikirim otomatis, mohon tidak membalas email ini.
              </p>
            </div>
          </body>
        </html>
        """
        
        return _send_email_via_resend(email, subject, html)
          
    except Exception as e:
        logger.error(f"Failed to send set password email to {email}: {str(e)}")
        raise Exception(f"Gagal mengirim email: {str(e)}")


def send_password_changed_notification(email: str, user_display_name: str = None):
    try:
        greeting = f"Halo {user_display_name}," if user_display_name else "Halo,"
        
        subject = f"{settings.MAIL_FROM_NAME} - Password Berhasil Diubah"
        
        now = datetime.now(timezone.utc)
        changed_at = now.strftime('%d %B %Y, %H:%M UTC')
        
        html = f"""
        <html>
          <body style="font-family: Arial, sans-serif; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #f9f9f9; padding: 30px; border-radius: 10px;">
              <h2 style="color: #333;"> Password Berhasil Diubah</h2>
              <p>{greeting}</p>
              <p>Password akun Anda telah berhasil diubah pada <strong>{changed_at}</strong>.</p>
              
              <div style="background-color: #e8f5e9; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <p style="margin: 0; color: #2e7d32;">
                   Password Anda sekarang sudah diperbarui dan aktif.
                </p>
              </div>
              
              <p><strong>Informasi Keamanan:</strong></p>
              <ul style="color: #666;">
                <li>Jika Anda yang melakukan perubahan ini, tidak ada tindakan lebih lanjut yang diperlukan.</li>
                <li>Jika Anda TIDAK melakukan perubahan ini, segera hubungi administrator untuk mengamankan akun Anda.</li>
              </ul>
              
              <div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <p style="margin: 0; color: #856404;">
                   <strong>Perhatian:</strong> Untuk keamanan akun Anda, pastikan untuk tidak membagikan password kepada siapapun.
                </p>
              </div>
              
              <p style="color: #999; font-size: 12px; margin-top: 30px;">
                Email ini dikirim otomatis dari sistem {settings.MAIL_FROM_NAME}.<br>
                Jika ada pertanyaan, silakan hubungi administrator sistem.
              </p>
            </div>
          </body>
        </html>
        """
        
        return _send_email_via_resend(email, subject, html)
          
    except Exception as e:
        logger.error(f"Failed to send password changed notification to {email}: {str(e)}")
        return False

def send_registration_rejection_email(
    email: str, 
    user_display_name: str = None,
    rejection_notes: str = None
):
    try:
        greeting = f"Bapak/Ibu {user_display_name}" if user_display_name else "Bapak/Ibu"
        
        notes_section = ""
        if rejection_notes:
            notes_section = f"""
            <div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <p style="margin: 0; color: #856404; font-size: 14px;">
                    <strong>📝 Catatan:</strong><br>
                    {rejection_notes}
                </p>
            </div>
            """
        
        subject = "Status Verifikasi Akun Dashboard Monitoring Infrastruktur Jalan"
        
        html = f"""
        <html>
          <body style="font-family: Arial, sans-serif; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 30px; border-radius: 10px;">
              <p style="color: #333; margin-bottom: 20px;">Yang Terhormat {greeting},</p>
              
              <p style="color: #333; margin-bottom: 20px;">
                Mohon maaf permohonan akun Anda pada <strong>KANCANA Dashboard Analitik Infrastruktur Jalan</strong> ditolak.
              </p>
              
              {notes_section}
              
              <p style="color: #333; margin-bottom: 20px;">
                Silakan periksa kembali data diri Anda atau hubungi tim kami di 
                <a href="mailto:dashboardjalan@jabarprov.go.id" style="color: #4CAF50; text-decoration: none;">
                  dashboardjalan@jabarprov.go.id
                </a>
              </p>
              
              <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee;">
                <p style="color: #333; margin: 5px 0;">Hormat kami,</p>
                <p style="color: #333; margin: 5px 0; font-weight: bold;">Tim KANCANA</p>
                <p style="color: #666; margin: 5px 0; font-size: 13px;">Dashboard Analitik Infrastruktur Jalan</p>
              </div>
              
              <p style="color: #999; font-size: 11px; margin-top: 30px; text-align: center;">
                Email ini dikirim otomatis, mohon tidak membalas email ini.
              </p>
            </div>
          </body>
        </html>
        """
        
        return _send_email_via_resend(email, subject, html)
          
    except Exception as e:
        logger.error(f"Failed to send registration rejection email to {email}: {str(e)}")
        return False

def send_account_created_by_admin_email(
    email: str, 
    user_display_name: str,
    username: str,
    temporary_password: str
):
    try:
        greeting = f"Bapak/Ibu {user_display_name}" if user_display_name else "Bapak/Ibu"
        
        subject = "Akun Anda Telah Dibuat - Dashboard Infrastruktur Jalan"
        
        html = f"""
        <html>
          <body style="font-family: Arial, sans-serif; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 30px; border-radius: 10px;">
              <p style="color: #333; margin-bottom: 20px;">Yang Terhormat {greeting},</p>
              
              <p style="color: #333; margin-bottom: 20px;">
                <strong>Selamat!</strong> Akun Anda pada <strong>KANCANA Dashboard Analitik Infrastruktur Jalan</strong> telah dibuat oleh administrator.
              </p>
              
              <div style="background-color: #d4edda; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <p style="margin: 0; color: #155724;">
                  Akun Anda sudah aktif dan dapat digunakan
                </p>
              </div>
              
              <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="color: #333; margin-top: 0;">Informasi Login:</h3>
                <table style="width: 100%;">
                  <tr>
                    <td style="padding: 8px; font-weight: bold; width: 40%;">Username:</td>
                    <td style="padding: 8px;">{username}</td>
                  </tr>
                  <tr>
                    <td style="padding: 8px; font-weight: bold;">Password Sementara:</td>
                    <td style="padding: 8px; font-family: monospace; background: #fff; padding: 10px; border-radius: 4px;">{temporary_password}</td>
                  </tr>
                </table>
              </div>
              
              <div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <p style="margin: 0; color: #856404;">
                  <strong>Penting:</strong> Silakan login dan segera ubah password Anda melalui menu Profile.
                </p>
              </div>
              
              <div style="text-align: center; margin: 30px 0;">
                <a href="{settings.FRONTEND_URL}/login" 
                    style="background-color: #4CAF50; color: white; padding: 14px 40px; 
                          text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                  Login Sekarang
                </a>
              </div>
              
              <p style="color: #333; margin-top: 30px;">
                Terima kasih atas perhatian dan kerjasama Bapak/Ibu.
              </p>
              
              <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee;">
                <p style="color: #333; margin: 5px 0;">Hormat kami,</p>
                <p style="color: #333; margin: 5px 0; font-weight: bold;">Tim KANCANA</p>
                <p style="color: #666; margin: 5px 0; font-size: 13px;">Dashboard Analitik Infrastruktur Jalan</p>
              </div>
              
              <p style="color: #999; font-size: 11px; margin-top: 30px; text-align: center;">
                Email ini dikirim otomatis, mohon tidak membalas email ini.
              </p>
            </div>
          </body>
        </html>
        """
        
        return _send_email_via_resend(email, subject, html)
          
    except Exception as e:
        logger.error(f"Failed to send account created email to {email}: {str(e)}")
        return False
    