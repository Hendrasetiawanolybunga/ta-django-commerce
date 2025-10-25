from django import forms
from django.forms import inlineformset_factory
from admin_dashboard.models import Pelanggan, Produk, Kategori, DiskonPelanggan, Transaksi, DetailTransaksi

class PelangganForm(forms.ModelForm):
    tanggal_lahir = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False
    )
    
    class Meta:
        model = Pelanggan
        fields = ['nama_pelanggan', 'alamat', 'tanggal_lahir', 'no_hp', 'username', 'email', 'password']
        widgets = {
            'password': forms.PasswordInput(),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make password optional for edit forms
        if self.instance and self.instance.pk:
            self.fields['password'].required = False
        # Make username and email required
        self.fields['username'].required = True
        self.fields['email'].required = True
        # Add CSS classes for better styling
        for field in self.fields:
            if field != 'tanggal_lahir':  # Date field has special handling
                self.fields[field].widget.attrs.update({'class': 'form-control'})

class ProdukForm(forms.ModelForm):
    class Meta:
        model = Produk
        fields = ['nama_produk', 'deskripsi_produk', 'foto_produk', 'stok_produk', 'harga_produk', 'kategori']
        widgets = {
            'nama_produk': forms.TextInput(attrs={'class': 'form-control'}),
            'deskripsi_produk': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'foto_produk': forms.FileInput(attrs={'class': 'form-control'}),
            'stok_produk': forms.NumberInput(attrs={'class': 'form-control'}),
            'harga_produk': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'kategori': forms.Select(attrs={'class': 'form-control'}),
        }

class KategoriForm(forms.ModelForm):
    class Meta:
        model = Kategori
        fields = ['nama_kategori']

class DiskonForm(forms.ModelForm):
    class Meta:
        model = DiskonPelanggan
        fields = ['pelanggan', 'produk', 'persen_diskon', 'status', 'pesan']
        widgets = {
            'pesan': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make product optional
        self.fields['produk'].required = False
        # Set querysets for foreign key fields
        # Type checker may complain about objects attribute, but it's valid in Django
        self.fields['pelanggan'].queryset = Pelanggan.objects.all()  # type: ignore
        self.fields['produk'].queryset = Produk.objects.all()  # type: ignore
        # Add CSS classes
        self.fields['pelanggan'].widget.attrs.update({'class': 'form-control'})
        self.fields['produk'].widget.attrs.update({'class': 'form-control'})
        self.fields['persen_diskon'].widget.attrs.update({'class': 'form-control'})
        self.fields['status'].widget.attrs.update({'class': 'form-control'})

class TransaksiForm(forms.ModelForm):
    class Meta:
        model = Transaksi
        fields = ['pelanggan', 'status_transaksi', 'ongkir']
        widgets = {
            'status_transaksi': forms.Select(attrs={'class': 'form-control'}),
            'ongkir': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['pelanggan'].widget.attrs.update({'class': 'form-control'})
        self.fields['status_transaksi'].choices = [
            ('DIPROSES', 'Diproses'),
            ('DIBAYAR', 'Dibayar'),
            ('DIKIRIM', 'Dikirim'),
            ('SELESAI', 'Selesai'),
            ('DIBATALKAN', 'Dibatalkan'),
        ]

# Custom form for transaction details to handle existing records properly
class DetailTransaksiForm(forms.ModelForm):
    class Meta:
        model = DetailTransaksi
        fields = ['produk', 'jumlah_produk']
        widgets = {
            'produk': forms.Select(attrs={'class': 'form-control'}),
            'jumlah_produk': forms.NumberInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # For existing records, make fields not required
        # This allows editing the main transaction form without triggering validation errors on unchanged detail forms
        if self.instance and self.instance.pk:
            self.fields['produk'].required = False
            self.fields['jumlah_produk'].required = False

# Create a formset for transaction details with our custom form
DetailTransaksiFormSet = inlineformset_factory(
    Transaksi, DetailTransaksi,
    form=DetailTransaksiForm,
    fields=['produk', 'jumlah_produk'],
    extra=0,  # Show exactly the number of existing items, no extra forms
    widgets={
        'produk': forms.Select(attrs={'class': 'form-control'}),
        'jumlah_produk': forms.NumberInput(attrs={'class': 'form-control'}),
    }
)