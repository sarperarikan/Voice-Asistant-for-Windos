import os
import queue
import sounddevice as sd
import vosk
import json
import keyboard
import wx
import threading
import Levenshtein
import webbrowser  # URL'leri açmak için
from dotenv import load_dotenv  # .env dosyasını yüklemek için
import google.generativeai as genai  # Google AI için

# .env dosyasını yükle
load_dotenv()

# Google Gemini API yapılandırması
api_key = os.getenv('GOOGLE_API_KEY')
if not api_key:
    raise Exception("Google API Key is not set in .env file.")
genai.configure(api_key=api_key)
model = genai.GenerativeModel(model_name="gemini-1.5-pro-exp-0801", generation_config={"temperature": 1})

# Model yolunu burada belirtin (indirip çıkardığınız model dizini)
model_path = "vosk-model-small-tr-0.3"

# Vosk modelini yükleme
if not os.path.exists(model_path):
    print(f"Model dosyası {model_path} bulunamadı!")
    exit(1)

model_vosk = vosk.Model(model_path)

# Komut dosyasını oku
komut_dosyasi = "komutlar.txt"

def komutlari_oku():
    komutlar = []
    if os.path.exists(komut_dosyasi):
        with open(komut_dosyasi, 'r', encoding="utf-8") as file:
            for line in file:
                komut, kisa_yol = line.strip().split(":")
                komutlar.append((komut, kisa_yol))
    return komutlar

# Komutları Levenshtein ile karşılaştır
def en_yakin_komut(algilanan_komut, komutlar):
    en_iyi_uyum = None
    en_yakin = None
    for komut, kisa_yol in komutlar:
        mesafe = Levenshtein.distance(algilanan_komut, komut)
        if en_iyi_uyum is None or mesafe < en_iyi_uyum:
            en_iyi_uyum = mesafe
            en_yakin = (komut, kisa_yol)
    return en_yakin

# URL'yi aç
def open_url(url):
    webbrowser.open(url)

# Google Gemini API'sine istek gönderme
def gemini_api_istek(metin, frame):
    frame.update_text("Yanıt oluşturuluyor...")  # Yanıt süresince arayüzü kitlenmeden gösterilir
    try:
        content = {
            "parts": [
                {"text": metin}
            ]
        }
        response = model.generate_content([content])

        # Yanıtı kontrol et
        if response and hasattr(response, 'text'):
            return response.text  # GenerateContentResponse nesnesinin text alanını döndürüyoruz
        else:
            return "API’den boş bir yanıt geldi."
    except Exception as e:
        return f"API Hatası: {str(e)}"

# Ses kaydı ayarları
samplerate = 16000  # Modelin beklentisine uygun örnekleme oranı
q = queue.Queue()

# Mikrofonla ses verisini topla
def audio_callback(indata, frames, time, status):
    if status:
        print(status, flush=True)
    q.put(bytes(indata))

# Sesli komutları dinle ve uygula
def komut_dinle_ve_uygula(frame):
    komutlar = komutlari_oku()
    with sd.RawInputStream(samplerate=samplerate, blocksize=8000, dtype='int16', channels=1, callback=audio_callback):
        rec = vosk.KaldiRecognizer(model_vosk, samplerate)
        frame.update_text("Sesli komut algılamaya başlandı...")

        while frame.is_listening:
            data = q.get()
            if rec.AcceptWaveform(data):
                result = rec.Result()
                text = json.loads(result)["text"]
                frame.update_text(f"Algılanan komut: {text}")
                
                # Özel siteleri açmak için sesli komutları kontrol et
                if "arçelik web sayfası" in text.lower():
                    frame.update_text("www.arcelik.com açılıyor...")
                    open_url("https://www.arcelik.com")
                elif "grundig web sayfası" in text.lower():
                    frame.update_text("www.grundig.com açılıyor...")
                    open_url("https://www.grundig.com")
                elif "beko web sayfası" in text.lower():
                    frame.update_text("www.beko.com.tr açılıyor...")
                    open_url("https://www.beko.com.tr")
                else:
                    # Levenshtein ile en yakın komutu bul
                    yakin_komut = en_yakin_komut(text, komutlar)
                    if yakin_komut:
                        komut, kisa_yol = yakin_komut
                        frame.update_text(f"Klavye kısayolu uygulanıyor: {komut} -> {kisa_yol}")
                        keyboard.press_and_release(kisa_yol)
                    else:
                        frame.update_text("Tanımlı bir komut bulunamadı.")

# wxPython GUI Arayüzü
class MyFrame(wx.Frame):
    def __init__(self, parent, title):
        super(MyFrame, self).__init__(parent, title=title, size=(600, 400))

        panel = wx.Panel(self)
        notebook = wx.Notebook(panel)

        # Komut algılama durumu
        self.is_listening = False
        self.chat_history = []  # Sohbet geçmişi

        # Sekme 1: Sesli Komut Algılama
        self.page1 = wx.Panel(notebook)
        self.text_ctrl = wx.TextCtrl(self.page1, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.start_button = wx.Button(self.page1, label="Komutları Dinlemeye Başla (Ctrl+S)")
        self.start_button.Bind(wx.EVT_BUTTON, self.on_start_listening)

        self.stop_button = wx.Button(self.page1, label="Komutları Durdur (Ctrl+D)")
        self.stop_button.Bind(wx.EVT_BUTTON, self.on_stop_listening)

        vbox1 = wx.BoxSizer(wx.VERTICAL)
        vbox1.Add(self.text_ctrl, proportion=1, flag=wx.EXPAND | wx.ALL, border=10)
        vbox1.Add(self.start_button, flag=wx.ALIGN_CENTER | wx.ALL, border=10)
        vbox1.Add(self.stop_button, flag=wx.ALIGN_CENTER | wx.ALL, border=10)
        self.page1.SetSizer(vbox1)

        # Klavye kısayolları
        self.accel_tbl = wx.AcceleratorTable([
            (wx.ACCEL_CTRL, ord('S'), self.start_button.GetId()),
            (wx.ACCEL_CTRL, ord('D'), self.stop_button.GetId())
        ])
        self.SetAcceleratorTable(self.accel_tbl)

        # Sekme 2: Komut Ayarları
        self.page2 = wx.Panel(notebook)
        self.komut_list = wx.ListCtrl(self.page2, style=wx.LC_REPORT)
        self.komut_list.InsertColumn(0, "Komut", width=200)
        self.komut_list.InsertColumn(1, "Kısayol", width=200)
        self.load_commands()

        self.add_button = wx.Button(self.page2, label="Komut Ekle (Ctrl+E)")
        self.add_button.Bind(wx.EVT_BUTTON, self.on_add_command)

        vbox2 = wx.BoxSizer(wx.VERTICAL)
        vbox2.Add(self.komut_list, proportion=1, flag=wx.EXPAND | wx.ALL, border=10)
        vbox2.Add(self.add_button, flag=wx.ALIGN_CENTER | wx.ALL, border=10)
        self.page2.SetSizer(vbox2)

        # Sekme 3: Asistan Sekmesi
        self.page3 = wx.Panel(notebook)
        self.chat_ctrl = wx.TextCtrl(self.page3, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.input_ctrl = wx.TextCtrl(self.page3, style=wx.TE_PROCESS_ENTER)
        self.input_ctrl.Bind(wx.EVT_TEXT_ENTER, self.on_send_message)
        
        self.send_button = wx.Button(self.page3, label="Mesaj Gönder")
        self.send_button.Bind(wx.EVT_BUTTON, self.on_send_message)

        self.export_button = wx.Button(self.page3, label="Geçmişi Dışa Aktar")
        self.export_button.Bind(wx.EVT_BUTTON, self.on_export_chat)

        # Düzenlemeler ve ekran okuyucu uyumluluğu için eklenen tanımlayıcılar
        self.chat_ctrl.SetLabel("Sohbet ekranı")
        self.input_ctrl.SetLabel("Mesaj girin")
        self.send_button.SetLabel("Mesaj Gönder")
        self.export_button.SetLabel("Geçmişi Dışa Aktar")

        vbox3 = wx.BoxSizer(wx.VERTICAL)
        vbox3.Add(self.chat_ctrl, proportion=1, flag=wx.EXPAND | wx.ALL, border=10)
        vbox3.Add(self.input_ctrl, flag=wx.EXPAND | wx.ALL, border=10)
        vbox3.Add(self.send_button, flag=wx.ALIGN_CENTER | wx.ALL, border=5)
        vbox3.Add(self.export_button, flag=wx.ALIGN_CENTER | wx.ALL, border=5)
        self.page3.SetSizer(vbox3)

        # Not defteri sekmelerine sayfaları ekle
        notebook.AddPage(self.page1, "Sesli Komut Algılama")
        notebook.AddPage(self.page2, "Komut Ayarları")
        notebook.AddPage(self.page3, "Asistan")

        # Ana yerleşim düzeni
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(notebook, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)
        panel.SetSizer(vbox)

        self.Bind(wx.EVT_CLOSE, self.on_close)

    def update_text(self, message):
        self.text_ctrl.AppendText(message + "\n")

    def on_start_listening(self, event):
        # Komut dinleme işlemini başlat
        if not self.is_listening:
            self.is_listening = True
            self.thread = threading.Thread(target=komut_dinle_ve_uygula, args=(self,), daemon=True)
            self.thread.start()

    def on_stop_listening(self, event):
        # Komut dinlemeyi durdur
        if self.is_listening:
            self.is_listening = False
            self.update_text("Dinleme durduruldu.")

    def on_add_command(self, event):
        # Yeni komut ekle
        dlg = wx.TextEntryDialog(self, "Yeni Komut Girin (Komut:Kısayol)", "Komut Ekle")
        if dlg.ShowModal() == wx.ID_OK:
            yeni_komut = dlg.GetValue()
            with open(komut_dosyasi, 'a', encoding="utf-8") as file:
                file.write(yeni_komut + "\n")
            self.komut_list.DeleteAllItems()
            self.load_commands()

    def load_commands(self):
        # Komutlar dosyasını yükle ve listeye ekle
        komutlar = komutlari_oku()
        for komut, kisa_yol in komutlar:
            index = self.komut_list.InsertItem(self.komut_list.GetItemCount(), komut)
            self.komut_list.SetItem(index, 1, kisa_yol)

    def on_send_message(self, event):
        user_input = self.input_ctrl.GetValue()
        self.chat_ctrl.AppendText(f"Kullanıcı: {user_input}\n")
        self.chat_history.append(f"Kullanıcı: {user_input}")
        threading.Thread(target=self.process_message, args=(user_input,), daemon=True).start()

    def process_message(self, user_input):
        response = gemini_api_istek(user_input, self)
        self.chat_ctrl.AppendText(f"Asistan: {response}\n")
        self.chat_history.append(f"Asistan: {response}")

    def on_export_chat(self, event):
        # Sohbet geçmişini dışa aktar
        try:
            with open("chat_history.txt", 'w', encoding='utf-8') as f:
                for line in self.chat_history:
                    f.write(line + "\n")
            self.update_text("Konuşma geçmişi chat_history.txt dosyasına kaydedildi.")
            wx.MessageBox("Konuşma geçmişi başarıyla dışa aktarıldı!", "Başarılı", wx.OK | wx.ICON_INFORMATION)
        except Exception as e:
            wx.MessageBox(f"Hata: {str(e)}", "Hata", wx.OK | wx.ICON_ERROR)

    def on_close(self, event):
        self.Destroy()

class MyApp(wx.App):
    def OnInit(self):
        self.frame = MyFrame(None, title="Voice Access for Windows 2024")
        self.frame.Show()
        return True

# Ana uygulamayı başlat
if __name__ == "__main__":
    app = MyApp(False)
    app.MainLoop()
