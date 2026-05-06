// lib/screens/parent/bus_tracking_screen.dart
import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import '../../services/api_service.dart';
import '../../services/auth_provider.dart';

class BusTrackingScreen extends ConsumerStatefulWidget {
  final String busId;
  final String busName;
  const BusTrackingScreen({super.key, required this.busId, required this.busName});

  @override
  ConsumerState<BusTrackingScreen> createState() => _BusTrackingScreenState();
}

class _BusTrackingScreenState extends ConsumerState<BusTrackingScreen> {
  GoogleMapController? _mapController;
  LatLng? _busLocation;
  double _speed = 0;
  String _lastUpdated = '';
  bool _isOnline = false;
  late Timer _pollTimer;

  // School location (configure per school)
  static const LatLng _schoolLocation = LatLng(28.6139, 77.2090);

  @override
  void initState() {
    super.initState();
    _fetchLocation();
    // Poll every 10 seconds as WebSocket fallback
    _pollTimer = Timer.periodic(const Duration(seconds: 10), (_) => _fetchLocation());
  }

  @override
  void dispose() {
    _pollTimer.cancel();
    _mapController?.dispose();
    super.dispose();
  }

  Future<void> _fetchLocation() async {
    try {
      final api = ref.read(apiServiceProvider);
      final res = await api._dio.get('/bus/location/${widget.busId}');
      final data = res.data as Map<String, dynamic>;

      if (data['status'] == 'online' && data['location'] != null) {
        final loc = data['location'] as Map<String, dynamic>;
        final newPos = LatLng(
          (loc['lat'] as num).toDouble(),
          (loc['lng'] as num).toDouble(),
        );
        setState(() {
          _busLocation = newPos;
          _speed       = (loc['speed'] as num?)?.toDouble() ?? 0;
          _lastUpdated = loc['updated_at'] ?? '';
          _isOnline    = true;
        });
        // Animate camera to bus
        _mapController?.animateCamera(CameraUpdate.newLatLng(newPos));
      } else {
        setState(() => _isOnline = false);
      }
    } catch (e) {
      setState(() => _isOnline = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final busMarker = _busLocation != null
        ? {
            Marker(
              markerId: const MarkerId('bus'),
              position: _busLocation!,
              icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueBlue),
              infoWindow: InfoWindow(
                title: widget.busName,
                snippet: 'Speed: ${_speed.toStringAsFixed(0)} km/h',
              ),
            ),
            const Marker(
              markerId: MarkerId('school'),
              position: _schoolLocation,
              icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueGreen),
              infoWindow: InfoWindow(title: 'School'),
            ),
          }
        : <Marker>{};

    return Scaffold(
      appBar: AppBar(
        title: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(widget.busName, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold)),
          Row(children: [
            Container(
              width: 6, height: 6,
              margin: const EdgeInsets.only(right: 4),
              decoration: BoxDecoration(
                color: _isOnline ? Colors.green : Colors.red,
                shape: BoxShape.circle,
              ),
            ),
            Text(_isOnline ? 'Live' : 'Offline',
              style: TextStyle(fontSize: 11, color: _isOnline ? Colors.green : Colors.red)),
          ]),
        ]),
        backgroundColor: const Color(0xFF111827),
      ),
      body: Stack(
        children: [
          // Map
          GoogleMap(
            initialCameraPosition: CameraPosition(
              target: _busLocation ?? _schoolLocation,
              zoom: 14,
            ),
            markers: busMarker,
            onMapCreated: (c) => _mapController = c,
            mapType: MapType.normal,
            myLocationButtonEnabled: false,
            zoomControlsEnabled: false,
          ),

          // Status card
          Positioned(
            bottom: 16, left: 16, right: 16,
            child: Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: const Color(0xFF111827),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: const Color(0xFF374151)),
              ),
              child: Row(children: [
                Container(
                  width: 48, height: 48,
                  decoration: BoxDecoration(
                    color: const Color(0xFF4F46E5).withOpacity(0.1),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: const Color(0xFF4F46E5).withOpacity(0.3)),
                  ),
                  child: const Icon(Icons.directions_bus, color: Color(0xFF4F46E5), size: 24),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Text(widget.busName,
                      style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                    Text(
                      _isOnline
                        ? 'Speed: ${_speed.toStringAsFixed(0)} km/h'
                        : 'Bus location unavailable',
                      style: TextStyle(
                        color: _isOnline ? Colors.grey : Colors.red,
                        fontSize: 12),
                    ),
                  ]),
                ),
                IconButton(
                  icon: const Icon(Icons.refresh, color: Colors.grey, size: 20),
                  onPressed: _fetchLocation,
                ),
              ]),
            ),
          ),
        ],
      ),
    );
  }
}
