// Replaces MainPage.xaml.cs of a Blank App (Universal Windows); keep MainPage.xaml as is.

using System;
using System.Net.Http;
using Windows.Data.Json;
using Windows.Networking.PushNotifications;
using Windows.UI.Core;
using Windows.UI.Xaml;
using Windows.UI.Xaml.Controls;

namespace DPNTestbed
{
    public sealed partial class MainPage : Page
    {
        // the Mac's IP address; start scripts/server.py with --host 0.0.0.0
        const string Receiver = "http://192.168.0.10:8765";

        readonly HttpClient http = new HttpClient();
        readonly TextBlock status = new TextBlock { Text = "starting" };
        readonly ListView received = new ListView();

        public MainPage()
        {
            InitializeComponent();
            var panel = new StackPanel { Padding = new Thickness(16) };
            panel.Children.Add(status);
            panel.Children.Add(received);
            Content = panel;
            Start();
        }

        async void Start()
        {
            try
            {
                var channel = await PushNotificationChannelManager.CreatePushNotificationChannelForApplicationAsync();
                channel.PushNotificationReceived += OnPush;
                await http.PostAsync(Receiver + "/wns/channel", new StringContent(channel.Uri));
                status.Text = "ready";
            }
            catch (Exception e)
            {
                status.Text = "error: " + e.Message;
            }
        }

        async void OnPush(PushNotificationChannel sender, PushNotificationReceivedEventArgs e)
        {
            string content = "";
            if (e.NotificationType == PushNotificationType.Raw) content = e.RawNotification.Content;
            else if (e.NotificationType == PushNotificationType.Toast) content = e.ToastNotification.Content.GetXml();
            else if (e.NotificationType == PushNotificationType.Badge) content = e.BadgeNotification.Content.GetXml();
            else if (e.NotificationType == PushNotificationType.Tile) content = e.TileNotification.Content.GetXml();
            string type = e.NotificationType.ToString();

            var body = new JsonObject();
            body["source"] = JsonValue.CreateStringValue("wns");
            body["type"] = JsonValue.CreateStringValue(type);
            body["content"] = JsonValue.CreateStringValue(content);
            await Dispatcher.RunAsync(CoreDispatcherPriority.Normal, () => received.Items.Add(type + " " + content));
            try
            {
                await http.PostAsync(Receiver + "/received", new StringContent(body.Stringify()));
            }
            catch (Exception)
            {
                // the list on screen still shows it
            }
        }
    }
}
