function uploadImage(sId){
    return new Promise(function(resolve, reject){
        var formData = new FormData();
        formData.append("file", $('#'+sId).prop('files')[0]);
        console.log(formData)
        var url = "/upload/";
        $.ajax({
           type: "POST",
           url: url,
           data: formData,
           processData: false,
           contentType: false
        }).done(function(data){
            resolve(data);
        }).fail(function(data){
            reject(data);
        });
    });
}