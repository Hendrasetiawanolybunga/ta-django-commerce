from django import forms
from admin_dashboard.models import Pelanggan, Produk, Kategori, DiskonPelanggan

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

class ProdukForm(forms.ModelForm):
    class Meta:
        model = Produk
        fields = ['nama_produk', 'deskripsi_produk', 'foto_produk', 'stok_produk', 'harga_produk', 'kategori']
        widgets = {
            'deskripsi_produk': forms.Textarea(attrs={'rows': 4}),
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