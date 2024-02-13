function login() {
    let new_data = getValues('#data-items')
    $.ajax({
        type: 'POST',
        dataType: 'json',
        url: '/admin/login/',
        data: JSON.stringify(new_data),
        success: function (d) {
            if (d['_success'] === true) {
                location.href = '/api/'
            } else {
                alert(d['message'])
            }
        },
        error: function (d) {
            alert('errors')
        }
    });
    return false;
}

$(document).on('keypress', function (e) {
    if (e.which === 13) {
        login();
    }
});

