import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';

import '../../core/routes/app_routes.dart';
import '../../models/profile_model.dart';
import '../../services/api_service.dart';

class ProfileScreen extends StatefulWidget {
  final bool embeddedInShell;

  const ProfileScreen({
    super.key,
    this.embeddedInShell = false,
  });

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  final ApiService _apiService = ApiService();
  late Future<ProfileModel> _profileFuture;
  String _selectedCountry = '-';
  List<String> _savedLocations = [];
  List<String> _savedPaymentMethods = [];

  @override
  void initState() {
    super.initState();
    _profileFuture = _apiService.fetchProfile();
    _loadCountry();
    _loadPreferences();
  }

  Future<void> _loadCountry() async {
    final country = await _apiService.getSelectedCountry();
    if (!mounted) return;

    setState(() {
      _selectedCountry = country ?? '-';
    });
  }

  Future<void> _loadPreferences() async {
    final locations = await _apiService.getSavedPickupLocations();
    final methods = await _apiService.getSavedPaymentMethods();
    if (!mounted) return;
    setState(() {
      _savedLocations = locations;
      _savedPaymentMethods = methods;
    });
  }

  Future<void> _addLocation() async {
    final controller = TextEditingController();
    final value = await showDialog<String>(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text('Add pickup location'),
          content: TextField(
            controller: controller,
            decoration: const InputDecoration(hintText: 'e.g., Muscat Airport'),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Cancel'),
            ),
            ElevatedButton(
              onPressed: () => Navigator.pop(context, controller.text.trim()),
              child: const Text('Save'),
            ),
          ],
        );
      },
    );

    if (value == null || value.isEmpty) return;
    await _apiService.addSavedPickupLocation(value);
    await _loadPreferences();
  }

  Future<void> _logout() async {
    await _apiService.logout();

    if (!mounted) return;

    Navigator.pushNamedAndRemoveUntil(
      context,
      AppRoutes.login,
      (route) => false,
    );
  }

  Future<void> _changeCountry() async {
    Navigator.pushNamed(context, AppRoutes.countrySelection);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF6F7FB),
      appBar: AppBar(
        automaticallyImplyLeading: !widget.embeddedInShell,
        backgroundColor: Colors.white,
        elevation: 0,
        title: Text(
          'profile.title'.tr(),
          style: const TextStyle(
            color: Color(0xFF1C3566),
            fontWeight: FontWeight.w700,
            fontSize: 18,
          ),
        ),
        actions: [
          IconButton(
            onPressed: () {
              Navigator.pushNamed(context, AppRoutes.settings);
            },
            icon: const Icon(
              Icons.settings_outlined,
              color: Color(0xFF1C3566),
            ),
          ),
        ],
      ),
      body: FutureBuilder<ProfileModel>(
        future: _profileFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(
              child: CircularProgressIndicator(),
            );
          }

          if (snapshot.hasError || !snapshot.hasData) {
            return const Center(
              child: Text(
                'Failed to load profile',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                ),
              ),
            );
          }

          final profile = snapshot.data!;

          return SingleChildScrollView(
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
            child: Column(
              children: [
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(20),
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(24),
                    gradient: const LinearGradient(
                      begin: Alignment.centerLeft,
                      end: Alignment.centerRight,
                      colors: [
                        Color(0xFF234E8C),
                        Color(0xFF1D467E),
                        Color(0xFFD3AE52),
                      ],
                    ),
                    boxShadow: [
                      BoxShadow(
                        color: const Color(0xFF8E96A7).withAlpha(51),
                        blurRadius: 12,
                        offset: const Offset(0, 8),
                      ),
                    ],
                  ),
                  child: Column(
                    children: [
                      CircleAvatar(
                        radius: 34,
                        backgroundColor: Colors.white.withAlpha(51),
                        child: Text(
                          (profile.fullName.isNotEmpty
                                  ? profile.fullName[0]
                                  : profile.username.isNotEmpty
                                      ? profile.username[0]
                                      : 'U')
                              .toUpperCase(),
                          style: const TextStyle(
                            fontSize: 26,
                            fontWeight: FontWeight.w700,
                            color: Colors.white,
                          ),
                        ),
                      ),
                      const SizedBox(height: 14),
                      Text(
                        profile.fullName.isNotEmpty
                            ? profile.fullName
                            : profile.username,
                        textAlign: TextAlign.center,
                        style: const TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.w700,
                          color: Colors.white,
                        ),
                      ),
                      const SizedBox(height: 6),
                      Text(
                        profile.email.isNotEmpty
                            ? profile.email
                            : profile.username,
                        textAlign: TextAlign.center,
                        style: const TextStyle(
                          fontSize: 13,
                          color: Colors.white,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
                _infoCard(profile),
                const SizedBox(height: 16),
                _savedDataCard(),
                const SizedBox(height: 16),
                _quickActionsCard(context),
                const SizedBox(height: 16),
                SizedBox(
                  width: double.infinity,
                  height: 50,
                  child: ElevatedButton.icon(
                    onPressed: _logout,
                    icon: const Icon(Icons.logout_rounded),
                    label: Text(
                      'common.logout'.tr(),
                      style: const TextStyle(
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFFD14848),
                      foregroundColor: Colors.white,
                      elevation: 0,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(16),
                      ),
                    ),
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _infoCard(ProfileModel profile) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [Color(0xFFFFFFFF), Color(0xFFF6FAFF)],
        ),
        border: Border.all(color: const Color(0xFFDCE5F3)),
        borderRadius: BorderRadius.circular(22),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF9DA8BE).withAlpha(28),
            blurRadius: 16,
            offset: const Offset(0, 9),
          ),
        ],
      ),
      child: Column(
        children: [
          _row('profile.username'.tr(), profile.username),
          _row('profile.email'.tr(),
              profile.email.isNotEmpty ? profile.email : '-'),
          _row('profile.first_name'.tr(),
              profile.firstName.isNotEmpty ? profile.firstName : '-'),
          _row('profile.last_name'.tr(),
              profile.lastName.isNotEmpty ? profile.lastName : '-'),
          _row('profile.country'.tr(), _selectedCountry),
        ],
      ),
    );
  }

  Widget _quickActionsCard(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [Color(0xFFFFFFFF), Color(0xFFF6FAFF)],
        ),
        border: Border.all(color: const Color(0xFFDCE5F3)),
        borderRadius: BorderRadius.circular(22),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF9DA8BE).withAlpha(28),
            blurRadius: 16,
            offset: const Offset(0, 9),
          ),
        ],
      ),
      child: Column(
        children: [
          _actionTile(
            icon: Icons.public_rounded,
            title: 'profile.change_country'.tr(),
            onTap: _changeCountry,
          ),
          const Divider(height: 20),
          _actionTile(
            icon: Icons.description_outlined,
            title: 'profile.my_documents'.tr(),
            onTap: () {
              Navigator.pushNamed(context, AppRoutes.documents);
            },
          ),
          const Divider(height: 20),
          _actionTile(
            icon: Icons.credit_card_rounded,
            title: 'profile.payments'.tr(),
            onTap: () {
              Navigator.pushNamed(context, AppRoutes.payments);
            },
          ),
          const Divider(height: 20),
          _actionTile(
            icon: Icons.notifications_none_rounded,
            title: 'profile.notifications'.tr(),
            onTap: () {
              Navigator.pushNamed(context, AppRoutes.notifications);
            },
          ),
          const Divider(height: 20),
          _actionTile(
            icon: Icons.support_agent_rounded,
            title: 'Support Center',
            onTap: () {
              Navigator.pushNamed(context, AppRoutes.support);
            },
          ),
          const Divider(height: 20),
          _actionTile(
            icon: Icons.receipt_long_rounded,
            title: 'profile.booking_history'.tr(),
            onTap: () {
              Navigator.pushNamed(context, AppRoutes.bookingHistory);
            },
          ),
          const Divider(height: 20),
          _actionTile(
            icon: Icons.settings_outlined,
            title: 'profile.settings'.tr(),
            onTap: () {
              Navigator.pushNamed(context, AppRoutes.settings);
            },
          ),
        ],
      ),
    );
  }

  Widget _savedDataCard() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [Color(0xFFFFFFFF), Color(0xFFF6FAFF)],
        ),
        border: Border.all(color: const Color(0xFFDCE5F3)),
        borderRadius: BorderRadius.circular(22),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF9DA8BE).withAlpha(28),
            blurRadius: 16,
            offset: const Offset(0, 9),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Saved pickup locations',
            style: TextStyle(
              fontSize: 15,
              fontWeight: FontWeight.w700,
              color: Color(0xFF162E60),
            ),
          ),
          const SizedBox(height: 8),
          if (_savedLocations.isEmpty)
            const Text(
              'No saved locations yet.',
              style: TextStyle(color: Color(0xFF7B8192)),
            ),
          ..._savedLocations.map(
            (item) => Padding(
              padding: const EdgeInsets.only(bottom: 6),
              child: Text('- $item'),
            ),
          ),
          const SizedBox(height: 8),
          _actionButtonCard(
            label: 'Add location',
            icon: Icons.add_location_alt_outlined,
            onTap: _addLocation,
          ),
          const Divider(height: 24),
          const Text(
            'Saved payment methods',
            style: TextStyle(
              fontSize: 15,
              fontWeight: FontWeight.w700,
              color: Color(0xFF162E60),
            ),
          ),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: _savedPaymentMethods
                .map(
                  (method) => _paymentMethodPill(method),
                )
                .toList(),
          ),
          const SizedBox(height: 8),
          _actionButtonCard(
            label: 'Manage payment methods',
            icon: Icons.tune_rounded,
            onTap: () {
              Navigator.pushNamed(context, AppRoutes.settings);
            },
          ),
        ],
      ),
    );
  }

  Widget _actionTile({
    required IconData icon,
    required String title,
    required VoidCallback onTap,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(14),
      child: Row(
        children: [
          Icon(icon, color: const Color(0xFF234E8C)),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              title,
              style: const TextStyle(
                fontSize: 14.5,
                fontWeight: FontWeight.w600,
                color: Color(0xFF162E60),
              ),
            ),
          ),
          const Icon(
            Icons.arrow_forward_ios_rounded,
            size: 16,
            color: Color(0xFF9AA3B3),
          ),
        ],
      ),
    );
  }

  Widget _actionButtonCard({
    required String label,
    required IconData icon,
    required VoidCallback onTap,
  }) {
    return Material(
      color: Colors.transparent,
      borderRadius: BorderRadius.circular(16),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 11),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(16),
            gradient: const LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [Color(0xFFFFFFFF), Color(0xFFF4F8FF)],
            ),
            border: Border.all(color: const Color(0xFFD7E1F1)),
            boxShadow: [
              BoxShadow(
                color: const Color(0xFF9DA8BE).withAlpha(24),
                blurRadius: 9,
                offset: const Offset(0, 5),
              ),
            ],
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(icon, size: 18, color: const Color(0xFF2B5CA8)),
              const SizedBox(width: 8),
              Text(
                label,
                style: const TextStyle(
                  fontSize: 15,
                  fontWeight: FontWeight.w700,
                  color: Color(0xFF21406F),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _paymentMethodPill(String method) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(12),
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [Color(0xFFFFFFFF), Color(0xFFF5F8FE)],
        ),
        border: Border.all(color: const Color(0xFFD9E2F0)),
      ),
      child: Text(
        method,
        style: const TextStyle(
          fontSize: 13,
          fontWeight: FontWeight.w600,
          color: Color(0xFF1D3968),
        ),
      ),
    );
  }

  Widget _row(String title, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 14),
      child: Row(
        children: [
          SizedBox(
            width: 110,
            child: Text(
              title,
              style: const TextStyle(
                fontSize: 12.5,
                color: Color(0xFF7B8192),
              ),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: const TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w600,
                color: Color(0xFF162E60),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
