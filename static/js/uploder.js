function uploadImage(sId, sSize) {
    return new Promise(async function (resolve, reject) {
        let formData = new FormData();
        let file = $('#' + sId).prop('files')[0]
        formData.append("file", file);

        if (file.size && file.size < (sSize || 10000000)) {
            try {
                let response = await fetch('/upload/', {
                    method: 'POST',
                    body: formData
                });
                resolve(response.json());
            } catch (error) {
                reject(error);
            }
        } else {
            resolve({
                '_message': false,
                'message': 'Limit file: 10 Mb'
            })
        }
    });
}