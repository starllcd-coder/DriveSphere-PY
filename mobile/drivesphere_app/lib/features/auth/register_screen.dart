import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

import '../../core/config/app_config.dart';
import '../../core/routes/app_routes.dart';
import '../../core/utils/app_message_helper.dart';
import '../../services/api_service.dart';
import '../../widgets/app_primary_button.dart';
import '../../widgets/app_snackbar.dart';

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final ApiService _apiService = ApiService();

  final TextEditingController _fullNameController = TextEditingController();
  final TextEditingController _emailController = TextEditingController();
  final TextEditingController _phoneController = TextEditingController();
  final TextEditingController _passwordController = TextEditingController();
  final TextEditingController _nationalityController = TextEditingController();
  final TextEditingController _otpController = TextEditingController();

  bool _loading = false;
  bool _otpRequested = false;
  bool _otpVerified = false;
  bool get _googleAvailable =>
      !kIsWeb ||
      AppConfig.googleWebClientId.isNotEmpty ||
      AppConfig.googleServerClientId.isNotEmpty;
  bool get _appleAvailable => !kIsWeb;

  Future<void> _register() async {
    if (!_otpVerified) {
      AppSnackBar.error(context, 'Please verify your phone number first.');
      return;
    }
    setState(() => _loading = true);
    try {
      await _apiService.register(
        fullName: _fullNameController.text.trim(),
        email: _emailController.text.trim(),
        phone: _phoneController.text.trim(),
        password: _passwordController.text,
        nationality: _nationalityController.text.trim(),
      );
      if (!mounted) return;
      AppSnackBar.success(context, 'Account created successfully.');
      Navigator.pushNamedAndRemoveUntil(
        context,
        AppRoutes.appShell,
        (route) => false,
      );
    } catch (e) {
      if (!mounted) return;
      AppSnackBar.error(context, AppMessageHelper.extractErrorMessage(e));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _requestOtp() async {
    if (_phoneController.text.trim().isEmpty) {
      AppSnackBar.error(context, 'Please enter your phone number first.');
      return;
    }

    setState(() => _loading = true);
    try {
      final response =
          await _apiService.requestOtp(phone: _phoneController.text.trim());
      if (!mounted) return;
      setState(() {
        _otpRequested = true;
        _otpVerified = false;
      });
      final otp = response['otp']?.toString();
      if (AppConfig.enableDemoMode && otp != null && otp.isNotEmpty) {
        AppSnackBar.success(context, 'OTP sent. Use $otp in offline mode.');
      } else {
        AppSnackBar.success(context, 'OTP sent successfully.');
      }
    } catch (e) {
      if (!mounted) return;
      AppSnackBar.error(context, AppMessageHelper.extractErrorMessage(e));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _verifyOtp() async {
    if (!_otpRequested) {
      AppSnackBar.error(context, 'Please request OTP first.');
      return;
    }

    setState(() => _loading = true);
    try {
      final response = await _apiService.verifyOtp(
        phone: _phoneController.text.trim(),
        otp: _otpController.text.trim(),
      );
      if (!mounted) return;
      if (response['success'] == true) {
        setState(() => _otpVerified = true);
        AppSnackBar.success(context, 'Phone verified successfully.');
      } else {
        setState(() => _otpVerified = false);
        AppSnackBar.error(context, 'Invalid OTP code.');
      }
    } catch (e) {
      if (!mounted) return;
      AppSnackBar.error(context, AppMessageHelper.extractErrorMessage(e));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _providerSignIn(String provider) async {
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
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  void dispose() {
    _fullNameController.dispose();
    _emailController.dispose();
    _phoneController.dispose();
    _passwordController.dispose();
    _nationalityController.dispose();
    _otpController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF6F7FB),
      appBar: AppBar(
        title: const Text('Create account'),
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
        children: [
          _card(
            child: Column(
              children: [
                _field(_fullNameController, 'Full name'),
                const SizedBox(height: 12),
                _field(_emailController, 'Email'),
                const SizedBox(height: 12),
                _field(_phoneController, 'Phone number'),
                const SizedBox(height: 12),
                _field(_nationalityController, 'Nationality'),
                const SizedBox(height: 12),
                _field(_passwordController, 'Password', obscure: true),
                const SizedBox(height: 16),
                AppPrimaryButton(
                  label: 'Create account',
                  loading: _loading,
                  onPressed: _otpVerified ? () => _register() : null,
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          _card(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Phone verification (OTP)',
                  style: TextStyle(fontWeight: FontWeight.w700, fontSize: 16),
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    Expanded(
                      child: OutlinedButton(
                        onPressed: _loading ? null : _requestOtp,
                        child: const Text('Request OTP'),
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: _field(_otpController, 'OTP code'),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: ElevatedButton(
                        onPressed: _loading ? null : _verifyOtp,
                        child: const Text('Verify'),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          _card(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Continue with',
                  style: TextStyle(fontWeight: FontWeight.w700, fontSize: 16),
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    Expanded(
                      child: OutlinedButton.icon(
                        onPressed:
                            _loading ? null : () => _providerSignIn('Google'),
                        icon: const Icon(Icons.g_mobiledata_rounded),
                        label: const Text('Google'),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: OutlinedButton.icon(
                        onPressed:
                            _loading ? null : () => _providerSignIn('Apple'),
                        icon: const Icon(Icons.apple_rounded),
                        label: const Text('Apple'),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _field(
    TextEditingController controller,
    String label, {
    bool obscure = false,
  }) {
    return TextField(
      controller: controller,
      obscureText: obscure,
      decoration: InputDecoration(
        labelText: label,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
        ),
      ),
    );
  }

  Widget _card({required Widget child}) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [Color(0xFFFFFFFF), Color(0xFFF6FAFF)],
        ),
        border: Border.all(color: const Color(0xFFDCE5F3)),
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF9DA8BE).withAlpha(28),
            blurRadius: 14,
            offset: const Offset(0, 9),
          ),
        ],
      ),
      child: child,
    );
  }
}
