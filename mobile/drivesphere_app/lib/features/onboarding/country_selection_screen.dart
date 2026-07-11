import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';

import '../../core/constants/app_countries.dart';
import '../../core/routes/app_routes.dart';
import '../../services/api_service.dart';
import '../../widgets/app_snackbar.dart';

class CountrySelectionScreen extends StatefulWidget {
  const CountrySelectionScreen({super.key});

  @override
  State<CountrySelectionScreen> createState() => _CountrySelectionScreenState();
}

class _CountrySelectionScreenState extends State<CountrySelectionScreen> {
  final ApiService _apiService = ApiService();

  String? _selectedCountry;
  String _selectedLanguage = 'en';
  bool _saving = false;

  String _t(String en, String ar) {
    return context.locale.languageCode == 'ar' ? ar : en;
  }

  Future<void> _continue() async {
    if (_selectedCountry == null || _selectedCountry!.isEmpty) {
      AppSnackBar.error(
        context,
        _t('Please select a country first.', 'يرجى اختيار الدولة أولاً.'),
      );
      return;
    }

    setState(() => _saving = true);

    await _apiService.saveSelectedCountry(_selectedCountry!);
    await _apiService.saveSelectedLanguage(_selectedLanguage);
    if (!mounted) return;
    await context.setLocale(Locale(_selectedLanguage));

    final hasToken = await _apiService.hasToken();

    if (!mounted) return;

    Navigator.pushNamedAndRemoveUntil(
      context,
      hasToken ? AppRoutes.appShell : AppRoutes.login,
      (route) => false,
    );
  }

  @override
  Widget build(BuildContext context) {
    final countries = AppCountries.supported;

    return Scaffold(
      backgroundColor: const Color(0xFFF6F7FB),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(20, 18, 20, 24),
          child: Column(
            children: [
              const SizedBox(height: 10),
              Image.asset(
                'assets/images/logo.png',
                width: 110,
                errorBuilder: (_, __, ___) => const SizedBox.shrink(),
              ),
              const SizedBox(height: 18),
              Text(
                _t('Choose your country', 'اختر دولتك'),
                style: const TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.w700,
                  color: Color(0xFF162E60),
                ),
              ),
              const SizedBox(height: 8),
              Text(
                _t(
                  'Your country will set the marketplace region, currency, cities, and companies.',
                  'سيتم ضبط المنطقة والعملة والمدن وشركات التأجير حسب الدولة المختارة.',
                ),
                textAlign: TextAlign.center,
                style: const TextStyle(
                  fontSize: 13,
                  height: 1.6,
                  color: Color(0xFF687181),
                ),
              ),
              const SizedBox(height: 18),
              _languageSwitcher(),
              const SizedBox(height: 18),
              Expanded(
                child: ListView.separated(
                  itemCount: countries.length,
                  separatorBuilder: (_, __) => const SizedBox(height: 12),
                  itemBuilder: (context, index) {
                    final item = countries[index];
                    final isSelected = _selectedCountry == item.name;

                    return InkWell(
                      borderRadius: BorderRadius.circular(20),
                      onTap: () {
                        setState(() {
                          _selectedCountry = item.name;
                        });
                      },
                      child: Container(
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(20),
                          border: Border.all(
                            color: isSelected
                                ? const Color(0xFF234E8C)
                                : const Color(0xFFE1E7F0),
                            width: isSelected ? 1.6 : 1,
                          ),
                          boxShadow: [
                            BoxShadow(
                              color: const Color(0xFFB7C0D1).withAlpha(36),
                              blurRadius: 12,
                              offset: const Offset(0, 8),
                            ),
                          ],
                        ),
                        child: Row(
                          children: [
                            Text(item.flag,
                                style: const TextStyle(fontSize: 28)),
                            const SizedBox(width: 14),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    _selectedLanguage == 'ar'
                                        ? item.arabicName
                                        : item.name,
                                    style: const TextStyle(
                                      fontSize: 15,
                                      fontWeight: FontWeight.w700,
                                      color: Color(0xFF162E60),
                                    ),
                                  ),
                                  const SizedBox(height: 4),
                                  Text(
                                    '${_t('Currency', 'العملة')}: ${item.currencyCode} • ${_t('Cities', 'المدن')}: ${item.cities.length}',
                                    style: const TextStyle(
                                      fontSize: 12.5,
                                      color: Color(0xFF687181),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            if (isSelected)
                              const Icon(
                                Icons.check_circle_rounded,
                                color: Color(0xFF234E8C),
                              ),
                          ],
                        ),
                      ),
                    );
                  },
                ),
              ),
              const SizedBox(height: 16),
              SizedBox(
                width: double.infinity,
                height: 52,
                child: DecoratedBox(
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(18),
                    gradient: const LinearGradient(
                      begin: Alignment.centerLeft,
                      end: Alignment.centerRight,
                      colors: [Color(0xFF234E8C), Color(0xFFD3AE52)],
                    ),
                  ),
                  child: ElevatedButton(
                    onPressed: _saving ? null : _continue,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.transparent,
                      shadowColor: Colors.transparent,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(18),
                      ),
                    ),
                    child: _saving
                        ? const SizedBox(
                            width: 22,
                            height: 22,
                            child: CircularProgressIndicator(
                              strokeWidth: 2.3,
                              color: Colors.white,
                            ),
                          )
                        : Text(
                            _t('Continue', 'متابعة'),
                            style: const TextStyle(
                              fontSize: 15,
                              fontWeight: FontWeight.w700,
                              color: Colors.white,
                            ),
                          ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _languageSwitcher() {
    return Container(
      padding: const EdgeInsets.all(5),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: const Color(0xFFE2E8F2)),
      ),
      child: Row(
        children: [
          Expanded(
            child: _langButton(
              code: 'en',
              label: 'English',
            ),
          ),
          Expanded(
            child: _langButton(
              code: 'ar',
              label: 'العربية',
            ),
          ),
        ],
      ),
    );
  }

  Widget _langButton({
    required String code,
    required String label,
  }) {
    final selected = _selectedLanguage == code;

    return InkWell(
      borderRadius: BorderRadius.circular(14),
      onTap: () async {
        setState(() => _selectedLanguage = code);
        await context.setLocale(Locale(code));
      },
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 180),
        padding: const EdgeInsets.symmetric(vertical: 12),
        decoration: BoxDecoration(
          color: selected ? const Color(0xFF234E8C) : Colors.transparent,
          borderRadius: BorderRadius.circular(14),
        ),
        child: Center(
          child: Text(
            label,
            style: TextStyle(
              color: selected ? Colors.white : const Color(0xFF234E8C),
              fontWeight: FontWeight.w700,
            ),
          ),
        ),
      ),
    );
  }
}
