// static/js/utils_compressao.js

// static/js/utils_compressao.js

// static/js/utils_compressao.js

async function configurarCompressaoFoto___(inputSelector, previewSelector) {
    const inputFoto = document.querySelector(inputSelector);
    // ... (o preview pode voltar se você usar createObjectURL, 
    // mas vamos focar no erro de memória)
    const preview = document.querySelector(previewSelector); 
    alert("Função de compressão de foto carregada.");

    if (!inputFoto) return;

    inputFoto.addEventListener("change", async (event) => {
        const file = event.target.files[0];
        if (!file) return;

        const maxAllowedMB = 2;
        const fileMB = file.size / (1024 * 1024);
        console.log(`📸 Tamanho do arquivo original: ${fileMB.toFixed(2)} MB`);

        if (fileMB > maxAllowedMB) {
            alert(`A imagem é muito grande (${fileMB.toFixed(2)} MB). O limite é ${maxAllowedMB} MB.`);
            inputFoto.value = "";
            return;
        }

        const options = {
            maxSizeMB: 0.5,
            maxWidthOrHeight: 800,
            useWebWorker: true,
            maxIteration: 8,
            initialQuality: 0.5,
            exifOrientation: true,
            fileType: 'image/jpeg',
        };

        // --- A NOVA LÓGICA DE TRY/CATCH ---
        let finalFile = file; // Começa assumindo que o arquivo final é o original
        let isCompressed = false;

        try {
            console.time("compress");
            const compressedBlob = await imageCompression(file, options);
            console.timeEnd("compress");

            // Se chegou aqui, a compressão funcionou!
            const newFileName = file.name.split('.').slice(0, -1).join('.') + '.jpg';
            
            finalFile = new File([compressedBlob], newFileName, {
                type: compressedBlob.type,
                lastModified: Date.now(),
            });
            isCompressed = true;

            console.log(
                `✅ Imagem comprimida de ${fileMB.toFixed(2)} MB → ${(finalFile.size / 1024 / 1024).toFixed(2)} MB`
            );

        } catch (error) {
            console.error("❌ Erro ao comprimir imagem:", error);

            // Verifica se é um erro de memória
            if (error.name === 'DOMException' || error.message.toLowerCase().includes('memory')) {
                // Erro de memória! Vamos usar o arquivo original.
                console.warn(
                    `⚠️ Falha de memória ao comprimir. Usando arquivo original de ${fileMB.toFixed(2)} MB.`
                );
                // 'finalFile' já é o 'file' original, então não precisamos fazer nada
                alert("Sua foto é muito grande para ser otimizada no celular. Ela será enviada no tamanho original.");
            } else {
                // Outro erro (ex: arquivo corrompido)
                alert("Houve um erro inesperado ao processar sua foto. Tente novamente.");
                inputFoto.value = "";
                return; // Sai da função
            }
        }

        // Agora, o 'finalFile' é ou o comprimido, ou o original
        // 1. Coloca o arquivo final no input
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(finalFile);
        inputFoto.files = dataTransfer.files;

        // 2. Mostra o preview (se houver) usando a técnica segura
        if (preview) {
            if (preview.src) {
                URL.revokeObjectURL(preview.src); // Limpa o preview antigo
            }
            preview.src = URL.createObjectURL(finalFile); // Usa o método seguro
            preview.style.display = "block";
        }
    });
}

// Função genérica para compressão + preview
async function configurarCompressaoFoto(inputSelector, previewSelector) {
    const inputFoto = document.querySelector(inputSelector);
    const preview = document.querySelector(previewSelector);

    if (!inputFoto) return;

    inputFoto.addEventListener("change", async (event) => {
        const file = event.target.files[0];
        if (!file) return;

        // ... (A verificação de tamanho máximo está ótima) ...
        const maxAllowedMB = 3;
        // ...

        // --- NOSSAS CORREÇÕES COMEÇAM AQUI ---

        // 1. Opções melhoradas para lidar com câmera
        const options = {
            maxSizeMB: 0.5,
            maxWidthOrHeight: 1024,
            useWebWorker: true,
            maxIteration: 8,
            initialQuality: 0.6,
        
            exifOrientation: true, // Corrige fotos que vêm "de lado"
            fileType: 'image/jpeg',  // Força a saída para JPEG (converte HEIC)
        };

        try {
            console.time("compress");
            const compressedBlob = await imageCompression(file, options);
            console.timeEnd("compress");

            // 2. Criar um novo nome de arquivo correto
            // Pega o nome original sem a extensão (ex: "image" de "image.heic")
            const originalName = file.name.split('.').slice(0, -1).join('.');
            // Adiciona a nova extensão correta
            const newFileName = originalName + '.jpg'; // Porque forçamos 'image/jpeg'

       
            const compressedFile = new File([compressedBlob], newFileName, {
                type: compressedBlob.type, // DEVE ser o tipo do blob comprimido
                lastModified: Date.now(),
            });
    

            // Substitui o arquivo original (seu código aqui está perfeito)
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(compressedFile);
            inputFoto.files = dataTransfer.files;

            // Preview
            if (preview) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    preview.src = e.target.result;
                    preview.style.display = "block";
                };
                reader.readAsDataURL(compressedBlob);
            }



            console.log(
                `✅ Imagem comprimida de ${(file.size / 1024 / 1024).toFixed(2)} MB → ${(compressedBlob.size / 1024 / 1024).toFixed(2)} MB`
            );
            } catch (error) {
                console.error("❌ Erro ao comprimir imagem:", error);
                
                let userMessage = "Erro ao processar a imagem. Tente novamente.";
                
                if (error.message.includes("memory") || error.name === "DOMException") {
                    userMessage = "A foto é muito grande e seu celular não tem memória suficiente para processá-la. Tente uma foto menor ou feche outros apps.";
                }

                alert(userMessage);
                inputFoto.value = "";
}
    });
}


// Função genérica para compressão + preview
async function configurarCompressaoFoto_(inputSelector, previewSelector) {
    const inputFoto = document.querySelector(inputSelector);
    const preview = document.querySelector(previewSelector);

    if (!inputFoto) return;

    inputFoto.addEventListener("change", async (event) => {
        const file = event.target.files[0];
        if (!file) return;

        const maxAllowedMB = 10;
        const fileMB = file.size / (1024 * 1024);
        console.log(`📸 Tamanho do arquivo original: ${fileMB.toFixed(2)} MB`);

        if (fileMB > maxAllowedMB) {
            alert(`A imagem é muito grande (${fileMB.toFixed(2)} MB). Tente uma menor que ${maxAllowedMB} MB.`);
            inputFoto.value = "";
            return;
        }

        const options = {
            maxSizeMB: 1,
            maxWidthOrHeight: 1024,
            useWebWorker: true,
            maxIteration: 8,
            initialQuality: 0.8,
        };

        try {
            console.time("compress");
            const compressedBlob = await imageCompression(file, options);
            console.timeEnd("compress");

            // Blob → File
            const compressedFile = new File([compressedBlob], file.name, {
                type: file.type,
                lastModified: Date.now(),
            });

            // Substitui o arquivo original
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(compressedFile);
            inputFoto.files = dataTransfer.files;

            // Preview
            if (preview) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    preview.src = e.target.result;
                    preview.style.display = "block";
                };
                reader.readAsDataURL(compressedBlob);
            }

            console.log(
                `✅ Imagem comprimida de ${(file.size / 1024 / 1024).toFixed(2)} MB → ${(compressedBlob.size / 1024 / 1024).toFixed(2)} MB`
            );
        } catch (error) {
            console.error("❌ Erro ao comprimir imagem:", error);
            alert("Erro ao processar a imagem. Tente novamente ou selecione uma menor.");
            inputFoto.value = "";
        }
    });
}
