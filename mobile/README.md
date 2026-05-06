# 📱 SchoolSaaS Flutter App — Module 4

## Setup Steps

### Prerequisites
```bash
# Install Flutter SDK
https://docs.flutter.dev/get-started/install

# Verify install
flutter doctor
```

### 1. Install Dependencies
```bash
cd school-saas/mobile
flutter pub get
```

### 2. Set API URL
Edit `lib/services/api_service.dart`:
```dart
const String _baseUrl = 'https://your-app.railway.app/api';
```

### 3. Firebase Setup (for push notifications)
1. Go to https://console.firebase.google.com
2. Create project → Add Android app (package: com.schoolsaas.app)
3. Download `google-services.json` → place in `android/app/`
4. Add iOS app → download `GoogleService-Info.plist` → place in `ios/Runner/`

### 4. Run App
```bash
# Android
flutter run

# iOS
cd ios && pod install && cd ..
flutter run
```

### 5. Build APK (Android)
```bash
flutter build apk --release
# APK: build/app/outputs/flutter-apk/app-release.apk
```

### 6. Build iOS (Mac only)
```bash
flutter build ios --release
# Then upload via Xcode
```

---

## App Structure

```
lib/
├── main.dart              ← App entry, router, theme
├── services/
│   ├── api_service.dart   ← All API calls (Dio + secure storage)
│   └── auth_provider.dart ← Login state (Riverpod)
└── screens/
    ├── auth/login_screen.dart
    ├── admin/admin_shell.dart
    ├── teacher/teacher_shell.dart   ← Attendance marking
    ├── student/student_shell.dart   ← Video player (YT)
    └── parent/parent_shell.dart
```

## Security Features
- ✅ Tokens stored in iOS Keychain / Android Keystore
- ✅ Auto token refresh on 401
- ✅ Biometric auth on app foreground
- ✅ Never stores tokens in SharedPreferences
- ✅ YouTube videos shown as secure embed only

## Free Testing
Test on physical device or emulator — no cost.
For production: Google Play ($25 one-time) or Apple AppStore ($99/year).
