var server = {

    url: '/admin/struct/',

    get: function (sUrl, oData, callback_success, callback_error) {
        $.ajax({
            dataType: "json",
            url: sUrl,
            data: oData,
            success: function (oResponse) {
                if (callback_success != undefined && callback_success)
                    callback_success(oResponse);
            },
            error: function (oResponse) {
                if (callback_error != undefined && callback_error)
                    callback_error(oResponse);
            }
        });
    },

    post: function (sUrl, oData, callback_success, callback_error) {
        $.ajax({
            url: sUrl,
            type: 'post',
            data: oData,
            dataType: 'json',
            success: function (oResponse) {
                if (oResponse['_success']) {
                    if (callback_success != undefined && callback_success)
                        callback_success(oResponse);
                } else {
                    if (oResponse['_reason'] == 'limit_exceeded') {
                        alert("Лимит изчерпан");
                    }
                }
            },
            error: function (oResponse) {
                if (callback_error != undefined && callback_error)
                    callback_error(oResponse);
            }
        });
    },

    set: function (sKey, sValue) {
        server[sKey] = sValue;
    }
}

var oData = {};

function getValues(sContainer) {
    oData = {};
    $(sContainer + ' input').each(function (a, b) {
        oData[$(b).attr('name')] = $(b).val();
    })
    $(sContainer + ' textarea').each(function (a, b) {
        oData[$(b).attr('name')] = $(b).val();
    })
    $(sContainer + ' select').each(function (a, b) {
        oData[$(b).attr('name')] = $(b).val();
    });
    return oData;
}