(function($) {
    'use strict';
    
    // Pastikan jQuery tersedia
    if (typeof $ === 'undefined' && typeof django !== 'undefined') {
        $ = django.jQuery;
    }

    $(document).ready(function() {
        var productCount = 1;

        // Buka modal dan muat form
        $('#transactionModal').on('show.bs.modal', function() {
            var modal = $(this);
            $.ajax({
                url: modal.data('url'),
                type: 'GET',
                success: function(response) {
                    modal.html(response.html_content);
                    // Inisialisasi kembali productCount jika modal dimuat ulang
                    productCount = 1;
                },
                error: function() {
                    alert('Gagal memuat form transaksi.');
                }
            });
        });

        // Tangani klik tombol "Tambah Produk"
        $(document).on('click', '#add-product', function() {
            var productItem = $('.product-item').first().clone();
            productItem.find('select, input').each(function() {
                var name = $(this).attr('name');
                if (name) {
                    var newName = name.replace(/_(\d+)/, '_' + productCount);
                    $(this).attr('name', newName);
                    if ($(this).is('select')) {
                        $(this).val('');
                    } else {
                        $(this).val('1');
                    }
                }
            });
            productItem.find('.remove-product').show();
            $('#product-list').append(productItem);
            productCount++;
        });

        // Tangani klik tombol "Hapus Produk"
        $(document).on('click', '.remove-product', function() {
            if ($('.product-item').length > 1) {
                $(this).closest('.product-item').remove();
            }
        });

        // Tangani pengiriman form
        $(document).on('submit', '#transactionForm', function(e) {
            e.preventDefault();
            var form = $(this);
            var url = form.attr('action');

            $.ajax({
                url: url,
                type: 'POST',
                data: form.serialize(),
                beforeSend: function(xhr) {
                    xhr.setRequestHeader("X-CSRFToken", $('[name=csrfmiddlewaretoken]').val());
                },
                success: function(response) {
                    if (response.status === 'success') {
                        alert(response.message);
                        $('#transactionModal').modal('hide');
                        location.reload(); 
                    } else {
                        alert('Gagal: ' + response.message);
                    }
                },
                error: function(xhr, status, error) {
                    var response = JSON.parse(xhr.responseText);
                    alert('Terjadi kesalahan: ' + response.message);
                }
            });
        });
    });
})(django.jQuery);