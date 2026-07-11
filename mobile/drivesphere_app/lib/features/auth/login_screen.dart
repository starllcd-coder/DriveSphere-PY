import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

import '../../core/config/app_config.dart';
import '../../core/routes/app_routes.dart';
import '../../core/utils/app_message_helper.dart';
import '../../core/utils/app_validators.dart';
import '../../services/api_service.dart';
import '../../widgets/app_primary_button.dart';
import '../../widgets/app_snackbar.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final TextEditingController _identifierController =
      TextEditingController(text: 'drivesphere');
  final TextEditingController _passwordController =
      TextEditingController(text: 'password');

  final ApiService _apiService = ApiService();

  bool _loading = false;
  bool _obscurePassword = true;
  bool _rememberMe = true;

  bool get _googleAvailable =>
      !kIsWeb ||
      AppConfig.googleWebClientId.isNotEmpty ||
      AppConfig.googleServerClientId.isNotEmpty;

  bool get _appleAvailable => !kIsWeb;

  Future<void> _continueWithProvider(String provider) async {
    if (provider.toLowerCase() == 'google' && !_googleAvailable) {
      AppSnackBar.error(
        context,
        'Google sign-in is not configured for web. Set GOOGLE_WEB_CLIENT_ID.',
      );
      return;
    }
    if (provider.toLowerCase() == 'apple' && !_appleAvailable) {
      AppSnackBar.error(
        context,
        'Apple sign-in is not configured for web in this build.',
      );
      return;
    }
    setState(() => _loading = true);
    try {
      final ok = await _apiService.loginWithProvider(provider);
      if (!mounted) return;
      if (!ok) {
        AppSnackBar.error(
          context,
          'Could not complete $provider sign-in. Please check backend and provider config.',
        );
        return;
      }
      Navigator.pushNamedAndRemoveUntil(
        context,
        AppRoutes.appShell,
        (route) => false,
      );
    } catch (e) {
      if (!mounted) return;
      AppSnackBar.error(context, AppMessageHelper.extractErrorMessage(e));
    } finally {
      if (mounted) {
        setState(() => _loading = false);
      }
    }
  }

  Future<void> _requestPhoneOtp() async {
    final phone = _identifierController.text.trim();
    if (phone.isEmpty) {
      AppSnackBar.error(context, 'Enter your phone number first.');
      return;
    }
    setState(() => _loading = true);
    try {
      final response = await _apiService.requestOtp(phone: phone);
      if (!mounted) return;
      final otp = response['otp']?.toString();
      AppSnackBar.success(
        context,
        otp != null ? 'OTP sent. Offline code: $otp' : 'OTP sent successfully.',
      );
    } catch (e) {
      if (!mounted) return;
      AppSnackBar.error(context, AppMessageHelper.extractErrorMessage(e));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _login() async {
    FocusScope.of(context).unfocus();

    final identifierError = AppValidators.requiredField(
      _identifierController.text,
      'login.email_or_username'.tr(),
    );
    final passwordError = AppValidators.requiredField(
      _passwordController.text,
      'login.password'.tr(),
    );

    if (identifierError != null) {
      AppSnackBar.error(context, identifierError);
      return;
    }

    if (passwordError != null) {
      AppSnackBar.error(context, passwordError);
      return;
    }

    setState(() {
      _loading = true;
    });

    try {
      await _apiService.login(
        identifier: _identifierController.text.trim(),
        password: _passwordController.text.trim(),
      );

      if (!mounted) return;

      Navigator.pushNamedAndRemoveUntil(
        context,
        AppRoutes.appShell,
        (route) => false,
      );
    } catch (e) {
      if (!mounted) return;
      AppSnackBar.error(context, AppMessageHelper.extractErrorMessage(e));
    } finally {
      if (mounted) {
        setState(() {
          _loading = false;
        });
      }
    }
  }

  @override
  void dispose() {
    _identifierController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final isEn = context.locale.languageCode == 'en';

    return Scaffold(
      body: Container(
        width: double.infinity,
        height: double.infinity,
        color: const Color(0xFFF5F3F7),
        child: Stack(
          children: [
            Positioned.fill(
              child: Opacity(
                opacity: 0.96,
                child: Image.asset(
                  'assets/images/login_bg.png',
                  fit: BoxFit.cover,
                ),
              ),
            ),
            SafeArea(
              child: SingleChildScrollView(
                padding:
                    const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
                child: Column(
                  children: [
                    const SizedBox(height: 8),
                    _buildTopLogoSection(),
                    const SizedBox(height: 18),
                    _buildLoginCard(isEn),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTopLogoSection() {
    return Column(
      children: [
        Image.asset(
          'assets/images/logo.png',
          width: 120,
          fit: BoxFit.contain,
        ),
        const SizedBox(height: 6),
        Text(
          'app_name'.tr(),
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
          style: const TextStyle(
            fontSize: 22,
            fontWeight: FontWeight.w700,
            color: Color(0xFF1C3566),
            letterSpacing: -0.3,
          ),
        ),
        const SizedBox(height: 2),
        Text(
          'tagline'.tr(),
          textAlign: TextAlign.center,
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
          style: const TextStyle(
            fontSize: 10,
            fontWeight: FontWeight.w500,
            color: Color(0xFF4C4C58),
          ),
        ),
      ],
    );
  }

  Widget _buildLoginCard(bool isEn) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.white.withAlpha(87),
        borderRadius: BorderRadius.circular(26),
        border: Border.all(
          color: Colors.white.withAlpha(191),
          width: 1,
        ),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFFB8BBC7).withAlpha(46),
            blurRadius: 18,
            offset: const Offset(0, 10),
          ),
        ],
      ),
      child: Container(
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(22),
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [
              Colors.white.withAlpha(209),
              const Color(0xFFF3F1F7).withAlpha(194),
            ],
          ),
          border: Border.all(
            color: const Color(0xFFE6E3EC),
            width: 1,
          ),
        ),
        child: Stack(
          children: [
            Positioned.fill(
              child: ClipRRect(
                borderRadius: BorderRadius.circular(22),
                child: Opacity(
                  opacity: 0.18,
                  child: Image.asset(
                    'assets/images/login_bg.png',
                    fit: BoxFit.cover,
                  ),
                ),
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 14, 16, 18),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Align(
                    alignment: isEn ? Alignment.topRight : Alignment.topLeft,
                    child: _buildLanguageToggle(isEn),
                  ),
                  const SizedBox(height: 10),
                  Center(
                    child: Text(
                      'login.welcome_back'.tr(),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        fontSize: 22,
                        fontWeight: FontWeight.w800,
                        color: Color(0xFF162E60),
                        letterSpacing: -0.4,
                      ),
                    ),
                  ),
                  const SizedBox(height: 2),
                  Center(
                    child: Text(
                      'login.welcome_back_ar'.tr(),
                      style: TextStyle(
                        fontFamily: isEn ? 'Cairo' : null,
                        fontSize: 20,
                        fontWeight: FontWeight.w700,
                        color: const Color(0xFFC9A24B),
                      ),
                    ),
                  ),
                  const SizedBox(height: 18),
                  _buildLabel('login.email_or_username'.tr()),
                  const SizedBox(height: 7),
                  _buildIdentifierField(),
                  const SizedBox(height: 14),
                  _buildLabel('login.password'.tr()),
                  const SizedBox(height: 7),
                  _buildPasswordField(),
                  const SizedBox(height: 14),
                  _buildRememberForgotRow(),
                  const SizedBox(height: 18),
                  AppPrimaryButton(
                    label: 'login.sign_in'.tr(),
                    loading: _loading,
                    onPressed: _login,
                  ),
                  const SizedBox(height: 14),
                  Row(
                    children: [
                      Expanded(
                        child: OutlinedButton.icon(
                          onPressed: _loading
                              ? null
                              : () => _continueWithProvider('Google'),
                          icon: const Icon(Icons.g_mobiledata_rounded),
                          label: const Text('Google'),
                        ),
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: OutlinedButton.icon(
                          onPressed: _loading
                              ? null
                              : () => _continueWithProvider('Apple'),
                          icon: const Icon(Icons.apple_rounded),
                          label: const Text('Apple'),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 10),
                  SizedBox(
                    width: double.infinity,
                    child: OutlinedButton.icon(
                      onPressed: _loading ? null : _requestPhoneOtp,
                      icon: const Icon(Icons.sms_outlined),
                      label: const Text('Sign in with phone OTP'),
                    ),
                  ),
                  const SizedBox(height: 8),
                  Center(
                    child: TextButton(
                      onPressed: () =>
                          Navigator.pushNamed(context, AppRoutes.register),
                      child: const Text('Create a new account'),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildLanguageToggle(bool isEn) {
    return Container(
      width: 94,
      height: 34,
      padding: const EdgeInsets.all(2.5),
      decoration: BoxDecoration(
        color: Colors.white.withAlpha(199),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: const Color(0xFFD9D7E1),
          width: 1,
        ),
      ),
      child: Row(
        children: [
          Expanded(
            child: GestureDetector(
              onTap: () => context.setLocale(const Locale('en')),
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 180),
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(16),
                  color: isEn ? const Color(0xFF234E8C) : Colors.transparent,
                ),
                child: Text(
                  'EN',
                  style: TextStyle(
                    fontSize: 11.5,
                    fontWeight: FontWeight.w700,
                    color: isEn ? Colors.white : const Color(0xFF9A9AA5),
                  ),
                ),
              ),
            ),
          ),
          Expanded(
            child: GestureDetector(
              onTap: () => context.setLocale(const Locale('ar')),
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 180),
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(16),
                  color: !isEn ? const Color(0xFF234E8C) : Colors.transparent,
                ),
                child: Text(
                  'AR',
                  style: TextStyle(
                    fontSize: 11.5,
                    fontWeight: FontWeight.w700,
                    color: !isEn ? Colors.white : const Color(0xFF9A9AA5),
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildLabel(String text) {
    return Text(
      text,
      maxLines: 1,
      overflow: TextOverflow.ellipsis,
      style: const TextStyle(
        fontSize: 12,
        fontWeight: FontWeight.w600,
        color: Color(0xFF43465A),
      ),
    );
  }

  Widget _buildIdentifierField() {
    return Container(
      height: 48,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(13),
        gradient: const LinearGradient(
          colors: [
            Color(0xFFF0F1FA),
            Color(0xFFF5F6FD),
          ],
        ),
        boxShadow: const [
          BoxShadow(
            color: Color(0xFFCFD3E2),
            blurRadius: 10,
            offset: Offset(0, 4),
          ),
        ],
      ),
      child: TextField(
        controller: _identifierController,
        style: const TextStyle(
          fontSize: 14,
          fontWeight: FontWeight.w500,
          color: Color(0xFF2B2F3B),
        ),
        decoration: InputDecoration(
          hintText: 'drivesphere',
          hintStyle: const TextStyle(
            color: Color(0xFF8F93A6),
            fontSize: 13,
          ),
          prefixIcon: const Icon(
            Icons.person_rounded,
            color: Color(0xFF8276B8),
            size: 20,
          ),
          border: _noBorder(),
          enabledBorder: _noBorder(),
          focusedBorder: _noBorder(),
          contentPadding: const EdgeInsets.symmetric(vertical: 13),
        ),
      ),
    );
  }

  Widget _buildPasswordField() {
    return Container(
      height: 48,
      decoration: BoxDecoration(
        color: Colors.white.withAlpha(235),
        borderRadius: BorderRadius.circular(13),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFFD7D6DD).withAlpha(77),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: TextField(
        controller: _passwordController,
        obscureText: _obscurePassword,
        style: const TextStyle(
          fontSize: 14,
          fontWeight: FontWeight.w600,
          color: Color(0xFF2B2F3B),
          letterSpacing: 1.0,
        ),
        decoration: InputDecoration(
          hintText: '••••••••••',
          hintStyle: const TextStyle(
            color: Color(0xFF8F93A6),
            fontSize: 13,
          ),
          prefixIcon: const Icon(
            Icons.lock_rounded,
            color: Color(0xFFD4AF37),
            size: 20,
          ),
          suffixIcon: IconButton(
            onPressed: () {
              setState(() {
                _obscurePassword = !_obscurePassword;
              });
            },
            icon: Icon(
              _obscurePassword
                  ? Icons.visibility_outlined
                  : Icons.visibility_off_outlined,
              color: const Color(0xFFB3B3BA),
              size: 19,
            ),
          ),
          border: _noBorder(),
          enabledBorder: _noBorder(),
          focusedBorder: _noBorder(),
          contentPadding: const EdgeInsets.symmetric(vertical: 13),
        ),
      ),
    );
  }

  Widget _buildRememberForgotRow() {
    return Row(
      children: [
        Expanded(
          child: GestureDetector(
            onTap: () {
              setState(() {
                _rememberMe = !_rememberMe;
              });
            },
            child: Row(
              children: [
                Container(
                  width: 16,
                  height: 16,
                  decoration: BoxDecoration(
                    color: _rememberMe
                        ? const Color(0xFF355C9A)
                        : Colors.transparent,
                    borderRadius: BorderRadius.circular(4),
                    border: Border.all(
                      color: const Color(0xFF6A88BC),
                      width: 1.2,
                    ),
                  ),
                  child: _rememberMe
                      ? const Icon(
                          Icons.check,
                          size: 11,
                          color: Colors.white,
                        )
                      : null,
                ),
                const SizedBox(width: 7),
                Expanded(
                  child: Text(
                    'login.remember_me'.tr(),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      fontSize: 11.5,
                      fontWeight: FontWeight.w500,
                      color: Color(0xFF4B4E5F),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(width: 8),
        TextButton(
          onPressed: () {
            AppSnackBar.info(context, 'login.forgot_password_info'.tr());
          },
          style: TextButton.styleFrom(
            padding: EdgeInsets.zero,
            minimumSize: Size.zero,
            tapTargetSize: MaterialTapTargetSize.shrinkWrap,
          ),
          child: Text(
            'login.forgot_password'.tr(),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(
              fontSize: 11.5,
              fontWeight: FontWeight.w500,
              color: Color(0xFF886C32),
            ),
          ),
        ),
      ],
    );
  }

  OutlineInputBorder _noBorder() {
    return OutlineInputBorder(
      borderRadius: BorderRadius.circular(14),
      borderSide: BorderSide.none,
    );
  }
}
