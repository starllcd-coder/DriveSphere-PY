import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';

import '../../core/constants/app_countries.dart';
import '../../core/routes/app_routes.dart';
import '../../services/api_service.dart';
import '../../widgets/app_snackbar.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  final ApiService _apiService = ApiService();

  String _selectedCountry = '-';
  String _selectedCurrency = '-';
  String _selectedCity = '-';
  bool _pushNotifications = true;
  bool _emailNotifications = true;
  final Set<String> _enabledPaymentMethods = {
    'CARD',
    'APPLE_PAY',
    'GOOGLE_PAY',
    'CASH_ON_PICKUP',
  };

  String _t(String en, String ar) {
    return context.locale.languageCode == 'ar' ? ar : en;
  }

  @override
  void initState() {
    super.initState();
    _loadSettings();
  }

  Future<void> _loadSettings() async {
    final country = await _apiService.getSelectedCountry();
    final city = await _apiService.getSelectedCity();
    final methods = await _apiService.getSavedPaymentMethods();
    final config = AppCountries.byName(country);

    if (!mounted) return;

    setState(() {
      _selectedCountry = country ?? config.name;
      _selectedCurrency = config.currencyCode;
      _selectedCity = city ?? config.cities.first;
      _enabledPaymentMethods
        ..clear()
        ..addAll(methods);
    });
  }

  Future<void> _togglePaymentMethod(String method, bool enabled) async {
    setState(() {
      if (enabled) {
        _enabledPaymentMethods.add(method);
      } else {
        _enabledPaymentMethods.remove(method);
      }
    });

    if (_enabledPaymentMethods.isEmpty) {
      _enabledPaymentMethods.add('CARD');
    }

    await _apiService.savePaymentMethods(_enabledPaymentMethods.toList());
  }

  Future<void> _changeLanguage(String code) async {
    await _apiService.saveSelectedLanguage(code);
    if (!mounted) return;
    await context.setLocale(Locale(code));

    if (!mounted) return;

    setState(() {});
    AppSnackBar.success(
      context,
      _t('Language updated successfully.', 'تم تحديث اللغة بنجاح.'),
    );
  }

  Future<void> _changeCity() async {
    final config = AppCountries.byName(_selectedCountry);

    final selected = await showModalBottomSheet<String>(
      context: context,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (context) {
        return SafeArea(
          child: ListView(
            shrinkWrap: true,
            padding: const EdgeInsets.all(16),
            children: config.cities.map((city) {
              return ListTile(
                title: Text(city),
                trailing: city == _selectedCity
                    ? const Icon(Icons.check_circle, color: Color(0xFF234E8C))
                    : null,
                onTap: () => Navigator.pop(context, city),
              );
            }).toList(),
          ),
        );
      },
    );

    if (selected == null) return;

    await _apiService.saveSelectedCity(selected);

    if (!mounted) return;
    setState(() => _selectedCity = selected);
    AppSnackBar.success(
      context,
      _t('Preferred city updated.', 'تم تحديث المدينة المفضلة.'),
    );
  }

  Future<void> _logout() async {
    await _apiService.logout();

    if (!mounted) return;
    Navigator.pushNamedAndRemoveUntil(context, AppRoutes.login, (_) => false);
  }

  @override
  Widget build(BuildContext context) {
    final isEn = context.locale.languageCode == 'en';

    return Scaffold(
      backgroundColor: const Color(0xFFF6F7FB),
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        title: Text(
          _t('Settings', 'الإعدادات'),
          style: const TextStyle(
            color: Color(0xFF1C3566),
            fontWeight: FontWeight.w700,
            fontSize: 18,
          ),
        ),
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
        children: [
          _sectionCard(
            title: _t('Marketplace preferences', 'تفضيلات السوق'),
            children: [
              _infoTile(
                icon: Icons.public_rounded,
                title: _t('Country', 'الدولة'),
                subtitle: _selectedCountry,
                onTap: () =>
                    Navigator.pushNamed(context, AppRoutes.countrySelection),
              ),
              const Divider(height: 20),
              _infoTile(
                icon: Icons.payments_outlined,
                title: _t('Currency', 'العملة'),
                subtitle: _selectedCurrency,
                onTap: () {},
              ),
              const Divider(height: 20),
              _infoTile(
                icon: Icons.location_city_outlined,
                title: _t('Preferred city', 'المدينة المفضلة'),
                subtitle: _selectedCity,
                onTap: _changeCity,
              ),
              const Divider(height: 20),
              _languageTile(isEn),
            ],
          ),
          const SizedBox(height: 16),
          _sectionCard(
            title: _t('Notifications', 'الإشعارات'),
            children: [
              SwitchListTile(
                value: _pushNotifications,
                onChanged: (value) =>
                    setState(() => _pushNotifications = value),
                title: Text(
                  _t('Push notifications', 'إشعارات الدفع'),
                  style: const TextStyle(
                    fontWeight: FontWeight.w600,
                    color: Color(0xFF162E60),
                  ),
                ),
                activeThumbColor: const Color(0xFF234E8C),
                contentPadding: EdgeInsets.zero,
              ),
              const Divider(height: 12),
              SwitchListTile(
                value: _emailNotifications,
                onChanged: (value) =>
                    setState(() => _emailNotifications = value),
                title: Text(
                  _t('Email notifications', 'إشعارات البريد الإلكتروني'),
                  style: const TextStyle(
                    fontWeight: FontWeight.w600,
                    color: Color(0xFF162E60),
                  ),
                ),
                activeThumbColor: const Color(0xFF234E8C),
                contentPadding: EdgeInsets.zero,
              ),
            ],
          ),
          const SizedBox(height: 16),
          _sectionCard(
            title: _t('Payment methods', 'طرق الدفع'),
            children: [
              _paymentMethodSwitch(
                  'CARD', _t('Credit/Debit Card', 'بطاقة ائتمان/مدى')),
              const Divider(height: 12),
              _paymentMethodSwitch('APPLE_PAY', 'Apple Pay'),
              const Divider(height: 12),
              _paymentMethodSwitch('GOOGLE_PAY', 'Google Pay'),
              const Divider(height: 12),
              _paymentMethodSwitch(
                  'CASH_ON_PICKUP', _t('Cash on pickup', 'الدفع عند الاستلام')),
            ],
          ),
          const SizedBox(height: 18),
          SizedBox(
            width: double.infinity,
            height: 50,
            child: ElevatedButton.icon(
              onPressed: _logout,
              icon: const Icon(Icons.logout_rounded),
              label: Text(
                _t('Logout', 'تسجيل الخروج'),
                style: const TextStyle(fontWeight: FontWeight.w700),
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
  }

  Widget _languageTile(bool isEn) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          _t('Language', 'اللغة'),
          style: const TextStyle(
            fontSize: 14.5,
            fontWeight: FontWeight.w600,
            color: Color(0xFF162E60),
          ),
        ),
        const SizedBox(height: 10),
        Row(
          children: [
            Expanded(
              child: _languageOption(
                label: 'English',
                selected: isEn,
                onTap: () => _changeLanguage('en'),
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: _languageOption(
                label: 'العربية',
                selected: !isEn,
                onTap: () => _changeLanguage('ar'),
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _languageOption({
    required String label,
    required bool selected,
    required VoidCallback onTap,
  }) {
    return InkWell(
      borderRadius: BorderRadius.circular(14),
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 12),
        decoration: BoxDecoration(
          color: selected ? const Color(0xFF234E8C) : const Color(0xFFF7F9FD),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(
            color: selected ? const Color(0xFF234E8C) : const Color(0xFFE2E8F2),
          ),
        ),
        child: Center(
          child: Text(
            label,
            style: TextStyle(
              color: selected ? Colors.white : const Color(0xFF162E60),
              fontWeight: FontWeight.w700,
            ),
          ),
        ),
      ),
    );
  }

  Widget _sectionCard({
    required String title,
    required List<Widget> children,
  }) {
    return Container(
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
          Text(
            title,
            style: const TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.w700,
              color: Color(0xFF162E60),
            ),
          ),
          const SizedBox(height: 14),
          ...children,
        ],
      ),
    );
  }

  Widget _paymentMethodSwitch(String method, String title) {
    return SwitchListTile(
      value: _enabledPaymentMethods.contains(method),
      onChanged: (value) => _togglePaymentMethod(method, value),
      title: Text(
        title,
        style: const TextStyle(
          fontWeight: FontWeight.w600,
          color: Color(0xFF162E60),
        ),
      ),
      activeThumbColor: const Color(0xFF234E8C),
      contentPadding: EdgeInsets.zero,
    );
  }

  Widget _infoTile({
    required IconData icon,
    required String title,
    required String subtitle,
    required VoidCallback onTap,
  }) {
    return InkWell(
      borderRadius: BorderRadius.circular(14),
      onTap: onTap,
      child: Row(
        children: [
          Icon(icon, color: const Color(0xFF234E8C)),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                    fontSize: 14.5,
                    fontWeight: FontWeight.w600,
                    color: Color(0xFF162E60),
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  subtitle,
                  style: const TextStyle(
                    fontSize: 12.5,
                    color: Color(0xFF687181),
                  ),
                ),
              ],
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
}
