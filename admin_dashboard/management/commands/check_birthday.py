from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date
from django.db.models import Sum
from admin_dashboard.models import Pelanggan, Notifikasi, Transaksi
from django.urls import reverse


class Command(BaseCommand):
    help = 'Check for customers with birthdays today and total spending >= 5 million'

    def handle(self, *args, **options):
        today = date.today()
        
        # Find ALL customers
        all_customers = Pelanggan.objects.all()
        
        for customer in all_customers:
            # Check if customer has birthday today
            is_birthday = (
                customer.tanggal_lahir and 
                customer.tanggal_lahir.month == today.month and 
                customer.tanggal_lahir.day == today.day
            )
            
            if not is_birthday:
                continue
            
            # Calculate total spending for paid transactions
            total_spending = Transaksi.objects.filter(
                pelanggan=customer,
                status_transaksi__in=['DIBAYAR', 'DIKIRIM', 'SELESAI']
            ).aggregate(
                total_belanja=Sum('total')
            )['total_belanja'] or 0
            
            # Check customer loyalty status
            is_loyal = total_spending >= 5000000
            
            # Check if notification already exists today for this customer (duplicate prevention)
            # We need to allow both P2-A and P2-B notifications, so check for specific message content
            existing_p2a_notification = Notifikasi.objects.filter(
                pelanggan=customer,
                tipe_pesan="Diskon Ulang Tahun Permanen",
                created_at__date=today
            ).first() if is_loyal else None
            
            existing_p2b_notification = Notifikasi.objects.filter(
                pelanggan=customer,
                tipe_pesan="Diskon Ulang Tahun Instan",
                created_at__date=today
            ).first() if not is_loyal else None
            
            # Print logging for debugging
            self.stdout.write(
                f'Checking customer {customer.nama_pelanggan} - Birthday: {is_birthday}, Loyal: {is_loyal}, Spending: {total_spending}'
            )
            
            # Always create notifications for eligible customers, but prevent duplicates
            should_send_p2a = is_loyal and not existing_p2a_notification
            should_send_p2b = not is_loyal and not existing_p2b_notification
            
            if should_send_p2a or should_send_p2b:
                # URL target for produk list page
                url_target = 'http://127.0.0.1:8000/produk/'
                
                # P2-A: Loyalitas Permanen (Loyal + Birthday)
                if should_send_p2a:
                    self.stdout.write(
                        f'Notifikasi dikirim untuk {customer.nama_pelanggan} (P2-A Loyal)'
                    )
                    # Create in-app notification with CTA URL for loyal customers
                    from admin_dashboard.views import create_notification
                    create_notification(
                        pelanggan=customer,
                        tipe_pesan="Diskon Ulang Tahun Permanen",
                        isi_pesan=f"Diskon 10% otomatis aktif pada 3 produk terfavorit Anda.",
                        url_target=url_target
                    )
                    
                    # Send email notification for loyal customers
                    from admin_dashboard.views import send_notification_email
                    try:
                        send_notification_email(
                            subject='Selamat Ulang Tahun! Diskon Spesial untuk Anda',
                            template_name='emails/birthday_discount_email.html',
                            context={
                                'customer': customer, 
                                'pesan_diskon': 'Selamat ulang tahun! Diskon 10% untuk Anda, silakan belanja agar diskon ini tidak hilang.',
                                'total_spending': total_spending
                            },
                            recipient_list=[customer.email],
                            url_target=url_target
                        )
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'Successfully notified loyal customer {customer.nama_pelanggan} about birthday discount'
                            )
                        )
                    except Exception as e:
                        self.stdout.write(
                            f'Failed to send email to {customer.nama_pelanggan}: {e}'
                        )
                # P2-B: Loyalitas Instan (Non-Loyal + Birthday)
                elif should_send_p2b:
                    self.stdout.write(
                        f'Notifikasi dikirim untuk {customer.nama_pelanggan} (P2-B Non-Loyal)'
                    )
                    # Create in-app notification with CTA URL for non-loyal customers
                    from admin_dashboard.views import create_notification
                    create_notification(
                        pelanggan=customer,
                        tipe_pesan="Diskon Ulang Tahun Instan",
                        isi_pesan=f"Raih Diskon 10% untuk SEMUA belanjaan hari ini jika total keranjang Anda mencapai Rp 5.000.000.",
                        url_target=url_target
                    )
                    
                    # Send email notification for non-loyal customers
                    from admin_dashboard.views import send_notification_email
                    try:
                        send_notification_email(
                            subject='Selamat Ulang Tahun! Kesempatan Diskon untuk Anda',
                            template_name='emails/birthday_discount_email.html',
                            context={
                                'customer': customer, 
                                'pesan_diskon': 'Raih Diskon 10% untuk SEMUA belanjaan hari ini jika total keranjang Anda mencapai Rp 5.000.000.',
                                'total_spending': total_spending
                            },
                            recipient_list=[customer.email],
                            url_target=url_target
                        )
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'Successfully notified non-loyal customer {customer.nama_pelanggan} about birthday opportunity'
                            )
                        )
                    except Exception as e:
                        self.stdout.write(
                            f'Failed to send email to {customer.nama_pelanggan}: {e}'
                        )
            else:
                self.stdout.write(
                    f'Notification already sent to {customer.nama_pelanggan} today'
                )