// Ses tanıma işlemlerini başlatmak ve durdurmak için gerekli fonksiyonlar
        function startRecognition() {
            // Annyang kütüphanesi ile ses tanıma işlemi başlatılabilir
            if (annyang) {
                annyang.setLanguage('tr-TR');
                annyang.start();
                document.getElementById('start-recognition').classList.add('d-none');
                document.getElementById('stop-recognition').classList.remove('d-none');
            }
        }

        function stopRecognition() {
            // Annyang kütüphanesi ile ses tanıma işlemi durdurulabilir
            if (annyang) {
                annyang.abort();
                document.getElementById('start-recognition').classList.remove('d-none');
                document.getElementById('stop-recognition').classList.add('d-none');
            }
        }

        // Sesli yazdırma işlemlerini başlatmak ve durdurmak için gerekli fonksiyonlar
        function startDictation() {
            if (annyang) {
                annyang.setLanguage('tr-TR');
                annyang.start({ continuous: true });
                document.getElementById('start-dictation').classList.add('d-none');
                document.getElementById('stop-dictation').classList.remove('d-none');

                annyang.addCallback('result', function(userSaid) {
                    const editor = document.getElementById('rich-text-editor');
                    editor.innerText += ' ' + userSaid[0]; // İlk sonucu ekle
                    showAlert('Sesli yazdırma aktif: ' + userSaid[0]);
                });
            }
        }

        function stopDictation() {
            if (annyang) {
                annyang.abort();
                document.getElementById('start-dictation').classList.remove('d-none');
                document.getElementById('stop-dictation').classList.add('d-none');
                showAlert('Sesli yazdırma durduruldu.');
            }
        }

        // Panoya kopyalama fonksiyonu
        function copyToClipboard() {
            const editor = document.getElementById('rich-text-editor');
            const text = editor.innerText;
            navigator.clipboard.writeText(text).then(() => {
                showAlert('Metin panoya kopyalandı.');
            }).catch(err => {
                showAlert('Panoya kopyalama başarısız oldu: ' + err);
            });
        }

        // Google'da arama yapma fonksiyonu
        function searchOnGoogle() {
            const editor = document.getElementById('rich-text-editor');
            const query = editor.innerText;
            const url = 'https://www.google.com/search?q=' + encodeURIComponent(query);
            window.open(url, '_blank');
            showAlert('Google üzerinde arama yapıldı.');
        }

        // Voice Assistant sunucusuna POST isteği gönderme
        function saveToWord() {
            const content = document.getElementById('rich-text-editor').innerText;
            fetch('/save_to_word', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ content: content })
            })
            .then(response => response.json())
            .then(data => {
                showAlert(data.message);
            })
            .catch(error => {
                console.error('Error:', error);
                showAlert('Word belgesi kaydedilirken bir hata oluştu.');
            });
        }

        // Sesli komutları işleme ve Python API'ye gönderme
        function executeVoiceCommand(command) {
            fetch('/execute_command', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ command: command })
            })
            .then(response => response.json())
            .then(data => {
                showAlert(data.message);
            })
            .catch(error => {
                console.error('Error:', error);
                showAlert('Komut yürütülürken bir hata oluştu.');
            });
        }

        function showDialog(message) {
            const dialogContainer = document.getElementById('dialog-container');
            const dialogMessage = document.getElementById('dialog-message');
            dialogMessage.innerText = message;
            dialogContainer.style.display = 'block';
            dialogContainer.setAttribute('aria-hidden', 'false');
        }

        function closeDialog() {
            const dialogContainer = document.getElementById('dialog-container');
            dialogContainer.style.display = 'none';
            dialogContainer.setAttribute('aria-hidden', 'true');
        }

        function showAlert(message) {
            showDialog(message);
        }

        // Komutları JSON dosyasından çekme ve tabloya ekleme
        function loadCommands() {
            fetch('/keyboard.json')
                .then(response => response.json())
                .then(commands => {
                    const tbody = document.getElementById('command-details-tbody');
                    tbody.innerHTML = '';
                    for (const command in commands) {
                        const tr = document.createElement('tr');
                        const tdCommand = document.createElement('td');
                        tdCommand.textContent = command;
                        const tdShortcut = document.createElement('td');
                        tdShortcut.textContent = commands[command];
                        tr.appendChild(tdCommand);
                        tr.appendChild(tdShortcut);
                        tbody.appendChild(tr);
                    }
                })
                .catch(error => {
                    console.error('Error loading commands:', error);
                });
        }

        // Sayfa yüklendiğinde komutları yükle
        document.addEventListener('DOMContentLoaded', loadCommands);

        // Annyang ile ses tanıma komutlarını tanımlama
        if (annyang) {
            const commands = {
                'kaydet': saveToWord,
                'başlat': startRecognition,
                'durdur': stopRecognition
            };
            annyang.addCommands(commands);

            annyang.addCallback('result', function(userSaid) {
                const resultElement = document.getElementById('result');
                const command = userSaid[0]; // İlk sonucu göster
                resultElement.innerText = command;
                executeVoiceCommand(command); // Sesli komutu Python API'ye gönder
            });
        }

        document.getElementById('start-recognition').addEventListener('click', startRecognition);
        document.getElementById('stop-recognition').addEventListener('click', stopRecognition);
        document.getElementById('start-dictation').addEventListener('click', startDictation);
        document.getElementById('stop-dictation').addEventListener('click', stopDictation);
