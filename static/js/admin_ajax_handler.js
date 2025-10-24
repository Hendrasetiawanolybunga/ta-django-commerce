// Standardized AJAX handler for admin dashboard modal operations
(function($) {
    'use strict';
    
    // Generic function to open a modal with AJAX content
    window.openModal = function(url, modalId, modalTitle) {
        const modal = $(modalId);
        const modalBody = modal.find('.modal-body');
        const modalTitleElement = modal.find('.modal-title');
        
        // Set modal title
        if (modalTitleElement && modalTitle) {
            modalTitleElement.text(modalTitle);
        }
        
        // Show loading indicator
        modalBody.html('<div class="text-center"><div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div></div>');
        
        // Load content via AJAX
        $.get(url)
            .done(function(data) {
                modalBody.html(data);
            })
            .fail(function() {
                modalBody.html('<div class="alert alert-danger">Error loading content.</div>');
            });
    };
    
    // Generic function to handle form submission via AJAX
    window.submitFormAjax = function(formSelector, successCallback) {
        $(document).on('submit', formSelector, function(e) {
            e.preventDefault();
            
            const form = $(this);
            const url = form.attr('action');
            const method = form.attr('method');
            const formData = new FormData(form[0]);
            
            $.ajax({
                url: url,
                type: method,
                data: formData,
                processData: false,
                contentType: false,
                success: function(response) {
                    if (response.success) {
                        // Hide modal
                        form.closest('.modal').modal('hide');
                        
                        // Show success message
                        showMessage(response.message, 'success');
                        
                        // Execute custom success callback if provided
                        if (successCallback && typeof successCallback === 'function') {
                            successCallback(response);
                        } else {
                            // Default behavior: reload page
                            location.reload();
                        }
                    } else {
                        // Show error message in modal
                        showFormError(form, response.message);
                    }
                },
                error: function() {
                    showFormError(form, 'An error occurred. Please try again.');
                }
            });
        });
    };
    
    // Generic function to handle delete operations
    window.handleDelete = function(url, successCallback) {
        if (confirm('Are you sure you want to delete this item?')) {
            $.ajax({
                url: url,
                type: 'POST',
                data: {
                    'csrfmiddlewaretoken': $('[name=csrfmiddlewaretoken]').val()
                },
                success: function(response) {
                    if (response.success) {
                        showMessage(response.message, 'success');
                        
                        // Execute custom success callback if provided
                        if (successCallback && typeof successCallback === 'function') {
                            successCallback(response);
                        } else {
                            // Default behavior: reload page
                            location.reload();
                        }
                    } else {
                        showMessage(response.message, 'danger');
                    }
                },
                error: function() {
                    showMessage('An error occurred. Please try again.', 'danger');
                }
            });
        }
    };
    
    // Function to fetch unread notifications
    window.fetchUnreadNotifications = function() {
        $.ajax({
            url: '/api/notifications/fetch/',
            type: 'GET',
            success: function(response) {
                if (response.success) {
                    // Update notification badge
                    const notificationBadge = $('#notification-badge');
                    if (notificationBadge.length) {
                        if (response.count > 0) {
                            notificationBadge.text(response.count).show();
                        } else {
                            notificationBadge.hide();
                        }
                    }
                    
                    // Render notifications if modal is open
                    if ($('#notificationModal').hasClass('show')) {
                        renderNotifications(response.notifications);
                    }
                }
            },
            error: function(xhr, status, error) {
                console.error('Error fetching notifications:', error);
            }
        });
    };
    
    // Function to mark notification as read
    window.markNotificationAsRead = function(notificationId, targetUrl) {
        $.ajax({
            url: '/api/notifications/mark_read/',
            type: 'POST',
            data: {
                'id': notificationId,
                'csrfmiddlewaretoken': $('[name=csrfmiddlewaretoken]').val()
            },
            success: function(response) {
                if (response.success) {
                    // Close modal
                    $('#notificationModal').modal('hide');
                    
                    // Redirect to target URL if provided
                    if (targetUrl && targetUrl !== '#') {
                        window.location.href = targetUrl;
                    } else if (response.target_url && response.target_url !== '#') {
                        window.location.href = response.target_url;
                    }
                    
                    // Refresh notification badge
                    fetchUnreadNotifications();
                } else {
                    showMessage(response.message || 'Error marking notification as read', 'danger');
                }
            },
            error: function(xhr, status, error) {
                console.error('Error marking notification as read:', error);
                showMessage('Error marking notification as read', 'danger');
            }
        });
    };
    
    // Function to render notifications in modal
    function renderNotifications(notifications) {
        const container = $('#notifications-container');
        if (!container.length) return;
        
        if (notifications.length === 0) {
            container.html('<p class="text-center text-muted">Tidak ada notifikasi baru</p>');
            return;
        }
        
        let html = '';
        notifications.forEach(function(notification) {
            html += `
                <div class="notification-item" onclick="markNotificationAsRead(${notification.id}, '${notification.target_url || '#'}')">
                    <div class="d-flex justify-content-between">
                        <span class="notification-title">${notification.tipe_pesan}</span>
                        <span class="notification-time">${formatNotificationTime(notification.created_at)}</span>
                    </div>
                    <div class="notification-content">${notification.isi_pesan}</div>
                </div>
            `;
        });
        
        container.html(html);
    }
    
    // Function to format notification time
    function formatNotificationTime(isoString) {
        const date = new Date(isoString);
        return date.toLocaleString('id-ID', {
            day: '2-digit',
            month: 'short',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }
    
    // Helper function to show messages
    function showMessage(message, type) {
        const alertHtml = `<div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>`;
        
        // Try to find a suitable place to show the message
        const messageContainer = $('.container-fluid, .container, .messages-container').first();
        if (messageContainer.length) {
            messageContainer.prepend(alertHtml);
        } else {
            $('body').prepend(alertHtml);
        }
    }
    
    // Helper function to show form errors
    function showFormError(form, message) {
        // Remove existing error messages
        form.find('.alert-danger').remove();
        
        // Add new error message
        form.prepend(`<div class="alert alert-danger">${message}</div>`);
    }
    
    // Initialize modal event handlers
    $(document).ready(function() {
        // Generic modal event handler
        $('.modal').on('show.bs.modal', function(event) {
            const button = $(event.relatedTarget);
            const action = button.data('action');
            const modal = $(this);
            
            // Clear previous content
            modal.find('.modal-body').html('<div class="text-center"><div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div></div>');
        });
        
        // Fetch notifications when notification modal is opened
        $('#notificationModal').on('show.bs.modal', function() {
            fetchUnreadNotifications();
        });
    });
    
})(jQuery);