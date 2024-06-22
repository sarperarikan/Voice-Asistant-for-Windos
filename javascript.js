document.addEventListener('DOMContentLoaded', (event) => {
    const tabs = document.querySelectorAll('.mdl-layout__tab');
    const panels = document.querySelectorAll('.mdl-layout__tab-panel');

    tabs.forEach((tab) => {
        tab.addEventListener('click', (e) => {
            e.preventDefault();
            tabs.forEach((t) => {
                t.classList.remove('is-active');
                t.removeAttribute('aria-current');
            });
            tab.classList.add('is-active');
            tab.setAttribute('aria-current', 'page');

            const targetId = tab.getAttribute('href').substring(1);
            panels.forEach((panel) => {
                if (panel.id === targetId) {
                    panel.classList.add('is-active');
                } else {
                    panel.classList.remove('is-active');
                }
            });
        });
    });

    document.querySelector('.mdl-layout__tab.is-active').setAttribute('aria-current', 'page');
    loadKeyboardCommands();
});

function startRecognition() {
    if (annyang) {
        annyang.setLanguage('tr-TR');
        annyang.start();
        showDialog('Ses tanıma etkin.');

        annyang.addCallback('result', function(phrases) {
            const command = phrases[0].toLowerCase();
            document.getElementById('result').innerText = command;
            window.pywebview.api.send_result(command);
        });

        annyang.addCallback('end', function() {
            showDialog('Ses tanıma sonlandı.');
        });

        annyang.addCallback('error', function() {
            showDialog('Ses tanıma sırasında bir hata oluştu.');
        });

        annyang.addCallback('start', function() {
            showDialog('Ses tanıma başladı.');
        });

        annyang.addCallback('soundstart', function() {
            showDialog('Ses algılandı.');
        });

        annyang.addCallback('errorNetwork', function() {
            showDialog('Ağ hatası. Lütfen internet bağlantınızı kontrol edin.');
        });

        annyang.addCallback('errorPermissionBlocked', function() {
            showDialog('Mikrofon izni engellendi.');
        });

        annyang.addCallback('errorPermissionDenied', function() {
            showDialog('Mikrofon izni reddedildi.');
        });
    } else {
        showDialog('Annyang desteklenmiyor.');
    }
}

function stopRecognition() {
    if (annyang) {
        annyang.abort();
        showDialog('Ses tanıma durduruldu.');
    } else {
        showDialog('Annyang desteklenmiyor.');
    }
}

function startDictation() {
    if (annyang) {
        annyang.setLanguage('tr-TR');
        annyang.start();
        showDialog('Sesli yazdırma etkin.');

        annyang.addCallback('result', function(phrases) {
            document.getElementById('rich-text-editor').innerText += ' ' + phrases[0].toLowerCase();
        });

        annyang.addCallback('end', function() {
            showDialog('Sesli yazdırma sonlandı.');
        });

        annyang.addCallback('error', function() {
            showDialog('Sesli yazdırma sırasında bir hata oluştu.');
        });

        annyang.addCallback('start', function() {
            showDialog('Sesli yazdırma başladı.');
        });

        annyang.addCallback('soundstart', function() {
            showDialog('Ses algılandı.');
        });

        annyang.addCallback('errorNetwork', function() {
            showDialog('Ağ hatası. Lütfen internet bağlantınızı kontrol edin.');
        });

        annyang.addCallback('errorPermissionBlocked', function() {
            showDialog('Mikrofon izni engellendi.');
        });

        annyang.addCallback('errorPermissionDenied', function() {
            showDialog('Mikrofon izni reddedildi.');
        });
    } else {
        showDialog('Annyang desteklenmiyor.');
    }
}

function stopDictation() {
    if (annyang) {
        annyang.abort();
        showDialog('Sesli yazdırma durduruldu.');
    } else {
        showDialog('Annyang desteklenmiyor.');
    }
}

function showDialog(message) {
    const dialogContainer = document.getElementById('dialog-container');
    const dialogMessage = document.getElementById('dialog-message');
    dialogMessage.innerText = message;
    dialogContainer.style.display = 'block';
}

function closeDialog() {
    const dialogContainer = document.getElementById('dialog-container');
    dialogContainer.style.display = 'none';
}

function loadKeyboardCommands() {
    fetch('/keyboard.json')
        .then(response => response.json())
        .then(commands => {
            const tbody = document.getElementById('command-details-tbody');
            tbody.innerHTML = ''; // Önceki içerikleri temizle

            for (const [command, shortcut] of Object.entries(commands)) {
                const tr = document.createElement('tr');
                const tdCommand = document.createElement('td');
                tdCommand.innerText = command;
                const tdShortcut = document.createElement('td');
                tdShortcut.innerText = shortcut;
                tr.appendChild(tdCommand);
                tr.appendChild(tdShortcut);
                tbody.appendChild(tr);
            }
        })
        .catch(error => {
            console.error('Error fetching the keyboard commands:', error);
        });
}

function saveToWord() {
    const content = document.getElementById('rich-text-editor').innerText;
    window.pywebview.api.save_to_word(content).then(response => {
        showDialog(response);
    });
}

function copyToClipboard() {
    const content = document.getElementById('rich-text-editor').innerText;
    navigator.clipboard.writeText(content).then(() => {
        showDialog('Metin panoya kopyalandı.');
    }).catch(err => {
        showDialog('Metin panoya kopyalanamadı.');
    });
}

function searchOnGoogle() {
    const content = document.getElementById('rich-text-editor').innerText;
    window.open(`https://www.google.com/search?q=${encodeURIComponent(content)}`, '_blank');
}
