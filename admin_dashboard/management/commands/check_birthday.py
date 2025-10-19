from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date
from django.db.models import Sum
from admin_dashboard.models import Pelanggan, Notifikasi, Transaksi

class Command(BaseCommand):
    help = 'Check for customers with birthdays today and total spending >= 5 million'

    def handle(self, *args, **options):
        today = date.today()
        
        # Find customers with birthdays today
        customers_with_birthday = Pelanggan.objects.filter(
            tanggal_lahir__month=today.month,
            tanggal_lahir__day=today.day
        )
        
        for customer in customers_with_birthday:
            # Calculate total spending for paid transactions
            total_spending = Transaksi.objects.filter(
                pelanggan=customer,
                status_transaksi__in=['DIBAYAR', 'DIKIRIM', 'SELESAI']
            ).aggregate(
                total_belanja=Sum('total')
            )['total_belanja'] or 0
            
            # Check if customer qualifies for birthday discount
            if total_spending >= 5000000:
                # Create in-app notification
                Notifikasi.objects.create(
                    pelanggan=customer,
                    tipe_pesan="Diskon Ulang Tahun",
                    isi_pesan=f"Selamat ulang tahun {customer.nama_pelanggan}! Anda berhak mendapatkan diskon 10% untuk pembelanjaan hari ini karena total belanja Anda sudah mencapai Rp {total_spending:,.0f}."
                )
                
                # Send email notification (simulated)
                from admin_dashboard.views import send_birthday_email
                send_birthday_email(customer, total_spending)
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully notified {customer.nama_pelanggan} about birthday discount'
                    )
                )
            else:
                self.stdout.write(
                    f'{customer.nama_pelanggan} has birthday today but does not qualify for discount (total: Rp {total_spending:,.0f})'
                )