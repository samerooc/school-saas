// lib/services/notification_service.dart
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:flutter/material.dart';

// Background message handler — must be top-level function
@pragma('vm:entry-point')
Future<void> _firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  // Handle background message
  debugPrint('Background message: ${message.messageId}');
}

class NotificationService {
  static final _fcm = FirebaseMessaging.instance;
  static final _localNotifications = FlutterLocalNotificationsPlugin();

  static const _androidChannel = AndroidNotificationChannel(
    'school_saas_channel',
    'SchoolSaaS Notifications',
    description: 'Attendance, fees, and school updates',
    importance: Importance.high,
  );

  static Future<void> init() async {
    // Request permission
    final settings = await _fcm.requestPermission(
      alert: true, badge: true, sound: true,
    );
    debugPrint('FCM permission: ${settings.authorizationStatus}');

    // Register background handler
    FirebaseMessaging.onBackgroundMessage(_firebaseMessagingBackgroundHandler);

    // Init local notifications
    const initSettings = InitializationSettings(
      android: AndroidInitializationSettings('@mipmap/ic_launcher'),
      iOS: DarwinInitializationSettings(),
    );
    await _localNotifications.initialize(
      initSettings,
      onDidReceiveNotificationResponse: _onNotificationTap,
    );

    // Create Android notification channel
    await _localNotifications
        .resolvePlatformSpecificImplementation<
            AndroidFlutterLocalNotificationsPlugin>()
        ?.createNotificationChannel(_androidChannel);

    // Handle foreground messages
    FirebaseMessaging.onMessage.listen(_handleForegroundMessage);

    // Handle notification tap when app in background
    FirebaseMessaging.onMessageOpenedApp.listen(_handleNotificationOpenedApp);

    // Get FCM token
    final token = await _fcm.getToken();
    debugPrint('FCM Token: $token');
    // TODO: Send token to backend: POST /api/users/fcm-token
  }

  static Future<void> _handleForegroundMessage(RemoteMessage message) async {
    final notification = message.notification;
    if (notification == null) return;

    // Show local notification when app is in foreground
    await _localNotifications.show(
      notification.hashCode,
      notification.title,
      notification.body,
      NotificationDetails(
        android: AndroidNotificationDetails(
          _androidChannel.id,
          _androidChannel.name,
          channelDescription: _androidChannel.description,
          importance: Importance.high,
          priority: Priority.high,
          icon: '@mipmap/ic_launcher',
        ),
        iOS: const DarwinNotificationDetails(
          presentAlert: true,
          presentBadge: true,
          presentSound: true,
        ),
      ),
      payload: message.data['route'],
    );
  }

  static void _handleNotificationOpenedApp(RemoteMessage message) {
    final route = message.data['route'];
    debugPrint('Notification opened app, route: $route');
    // TODO: Navigate to relevant screen based on route
    // e.g. 'fee_reminder' -> fees screen
    // e.g. 'attendance_alert' -> attendance screen
  }

  static void _onNotificationTap(NotificationResponse response) {
    final route = response.payload;
    debugPrint('Notification tapped, route: $route');
    // TODO: Navigate based on route
  }

  // Notification types sent from backend:
  // fee_reminder    → Student/Parent fee due alert
  // attendance_alert → Parent informed child absent
  // exam_notice     → Exam schedule published
  // bus_alert       → Bus arriving in 10 mins
  // new_message     → Chat message received
  // notice          → School-wide notice
}
