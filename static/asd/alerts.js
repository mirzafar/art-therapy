function alertShow(type, text, is_reload) {
    $('#alert-block').show()
    if (type === 'success') {
        $('#alert-success').css('display', 'block');
        $('#alert-success span').text(text || '')
        setTimeout(function () {
            $('#alert-success').css('display', 'none');
            $('#alert-block').hide()
        }, 1500);

    } else if (type === 'error') {
        $('#alert-error').css('display', 'block');
        $('#alert-error span').text(text)
        setTimeout(function () {
            $('#alert-error').css('display', 'none');
            $('#alert-block').hide()
        }, 3500);

        return

    } else if (type === 'waring') {
        $('#alert-waring').css('display', 'block');
        if (text) {
            $('#alert-waring span').text(text)
        }
        setTimeout(function () {
            $('#alert-waring').css('display', 'none');
            $('#alert-block').hide()
        }, 1500);
        return

    } else if (type === 'info') {
        $('#alert-info').css('display', 'block');
        $('#alert-info span').text(text)
        setTimeout(function () {
            $('#alert-info').css('display', 'none');
            $('#alert-block').hide()
        }, 2500);

        return
    }

    if (is_reload && is_reload === true) {
        setTimeout(function () {
            location.reload();
        }, 1000);
    }
}