import 'package:dio/dio.dart';
import 'package:flutter/material.dart';

import '../../core/config/app_config.dart';
import '../../core/routes/app_routes.dart';
import '../../core/session/session_store.dart';
import '../../services/staff_api_service.dart';
import '../../widgets/brand_background.dart';
import '../../widgets/brand_button.dart';
import '../../widgets/glass_panel.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen>
    with SingleTickerProviderStateMixin {
  final _identifierController = TextEditingController();
  final _passwordController = TextEditingController();
  final _identifierFocus = FocusNode();
  final _passwordFocus = FocusNode();
  final _session = SessionStore();
  final _api = StaffApiService();
  late final AnimationController _animController;
  late final Animation<double> _logoOpacity;
  late final Animation<Offset> _cardSlide;
  bool _loading = false;
  bool _obscurePassword = true;
  bool _rememberMe = true;
  String _error = '';

  void _onFocusChange() {
    if (!mounted) return;
    setState(() {});
  }

  @override
  void initState() {
    super.initState();
    _animController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 550),
    );
    _logoOpacity = CurvedAnimation(
      parent: _animController,
      curve: Curves.easeOut,
    );
    _cardSlide = Tween<Offset>(
      begin: const Offset(0, 0.06),
      end: Offset.zero,
    ).animate(
        CurvedAnimation(parent: _animController, curve: Curves.easeOutCubic));
    _identifierFocus.addListener(_onFocusChange);
    _passwordFocus.addListener(_onFocusChange);
    _loadSavedState();
    _animController.forward();
  }

  @override
  void dispose() {
    _identifierController.dispose();
    _passwordController.dispose();
    _identifierFocus.removeListener(_onFocusChange);
    _passwordFocus.removeListener(_onFocusChange);
    _identifierFocus.dispose();
    _passwordFocus.dispose();
    _animController.dispose();
    super.dispose();
  }

  Future<void> _loadSavedState() async {
    final remember = await _session.getRememberMe();
    final lastIdentifier = await _session.getLastIdentifier();
    if (!mounted) return;
    setState(() {
      _rememberMe = remember;
      _identifierController.text = lastIdentifier ?? '';
    });
  }

  String _humanizeError(Object e) {
    if (e is DioException) {
      if (e.response?.statusCode == 401) {
        return 'Invalid username or password.';
      }
      if (e.response?.statusCode == 400) {
        final payload = e.response?.data;
        if (payload is Map<String, dynamic>) {
          final errorText = payload['error']?.toString();
          if (errorText != null && errorText.trim().isNotEmpty) {
            if (errorText.toLowerCase().contains('invalid login request')) {
              return 'Invalid username or password.';
            }
            return errorText.trim();
          }
          final details = payload['details'];
          if (details is Map) {
            final flattened = details.values
                .map((v) => v is List ? v.join(', ') : v.toString())
                .where((v) => v.trim().isNotEmpty)
                .join('\n');
            if (flattened.isNotEmpty) return flattened;
          }
        }
        return 'Invalid username or password.';
      }
      if (e.type == DioExceptionType.connectionError ||
          e.type == DioExceptionType.connectionTimeout ||
          e.type == DioExceptionType.receiveTimeout ||
          e.type == DioExceptionType.sendTimeout) {
        return 'Unable to reach server. Check network/API URL and try again.';
      }
      final payload = e.response?.data;
      if (payload is Map<String, dynamic>) {
        final msg = payload['message']?.toString() ??
            payload['error']?.toString() ??
            payload['detail']?.toString();
        if (msg != null && msg.trim().isNotEmpty) return msg.trim();
      }
    }
    return e.toString().replaceFirst('Exception: ', '');
  }

  Future<void> _submit() async {
    final identifier = _identifierController.text.trim();
    final password = _passwordController.text.trim();
    if (identifier.isEmpty || password.isEmpty) {
      setState(() => _error = 'Username and password are required.');
      return;
    }

    setState(() {
      _loading = true;
      _error = '';
    });
    try {
      await _api.login(
        identifier: identifier,
        password: password,
        rememberMe: _rememberMe,
      );
      final payload = await _api.fetchBootstrap();
      if (!mounted) return;
      if (payload.branches.length > 1) {
        Navigator.pushReplacementNamed(
          context,
          AppRoutes.branchSelector,
          arguments: payload,
        );
        return;
      }
      Navigator.pushReplacementNamed(
        context,
        AppRoutes.shell,
        arguments: payload,
      );
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = _humanizeError(e));
    } finally {
      if (mounted) {
        setState(() => _loading = false);
      }
    }
  }

  Widget _animatedField({
    required bool focused,
    required Widget child,
  }) {
    return AnimatedContainer(
      duration: const Duration(milliseconds: 150),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(14),
        boxShadow: focused
            ? const [
                BoxShadow(
                  color: Color(0x332A6BC9),
                  blurRadius: 12,
                  offset: Offset(0, 3),
                ),
              ]
            : const [],
      ),
      child: child,
    );
  }

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final width = constraints.maxWidth;
        final isTablet = width >= 700;
        final contentMaxWidth = isTablet ? 560.0 : 420.0;
        final horizontalPadding = isTablet ? 36.0 : 22.0;
        final logoWidth = isTablet ? 250.0 : 190.0;
        final titleSize = isTablet ? 22.0 : 20.0;
        final fieldTextSize = isTablet ? 16.0 : 15.0;
        final footerSize = isTablet ? 15.0 : 13.0;
        final panelRadius = isTablet ? 30.0 : 26.0;

        return Scaffold(
          body: BrandBackground(
            child: SafeArea(
              child: Center(
                child: SingleChildScrollView(
                  padding: EdgeInsets.symmetric(
                    horizontal: horizontalPadding,
                    vertical: 22,
                  ),
                  child: ConstrainedBox(
                    constraints: BoxConstraints(maxWidth: contentMaxWidth),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        FadeTransition(
                          opacity: _logoOpacity,
                          child: Image.asset(
                            'assets/images/logo.png',
                            width: logoWidth,
                            fit: BoxFit.contain,
                          ),
                        ),
                        SizedBox(height: isTablet ? 30 : 24),
                        SlideTransition(
                          position: _cardSlide,
                          child: GlassPanel(
                            borderRadius: BorderRadius.circular(panelRadius),
                            padding: EdgeInsets.fromLTRB(
                              isTablet ? 30 : 22,
                              isTablet ? 24 : 18,
                              isTablet ? 30 : 22,
                              isTablet ? 18 : 14,
                            ),
                            child: Column(
                              children: [
                                Text(
                                  'DriveSphere Control Panel',
                                  textAlign: TextAlign.center,
                                  style: TextStyle(
                                    fontSize: titleSize,
                                    height: 1.2,
                                    fontWeight: FontWeight.w600,
                                    color: const Color(0xFF4A4F66),
                                  ),
                                ),
                                const SizedBox(height: 6),
                                const Text(
                                  'Admin / Staff Login',
                                  style: TextStyle(
                                    color: Color(0xFF6D748A),
                                    fontSize: 13,
                                    fontWeight: FontWeight.w500,
                                  ),
                                ),
                                SizedBox(height: isTablet ? 18 : 14),
                                _animatedField(
                                  focused: _identifierFocus.hasFocus,
                                  child: TextField(
                                    focusNode: _identifierFocus,
                                    controller: _identifierController,
                                    style: TextStyle(fontSize: fieldTextSize),
                                    decoration: const InputDecoration(
                                      hintText: 'Username',
                                      prefixIcon: Icon(
                                        Icons.person,
                                        color: Color(0xFF5A9BEE),
                                      ),
                                    ),
                                  ),
                                ),
                                const SizedBox(height: 10),
                                _animatedField(
                                  focused: _passwordFocus.hasFocus,
                                  child: TextField(
                                    focusNode: _passwordFocus,
                                    controller: _passwordController,
                                    obscureText: _obscurePassword,
                                    style: TextStyle(fontSize: fieldTextSize),
                                    decoration: InputDecoration(
                                      hintText: 'Password',
                                      prefixIcon: const Icon(
                                        Icons.lock,
                                        color: Color(0xFF747B91),
                                      ),
                                      suffixIcon: IconButton(
                                        onPressed: () {
                                          setState(() {
                                            _obscurePassword =
                                                !_obscurePassword;
                                          });
                                        },
                                        icon: Icon(
                                          _obscurePassword
                                              ? Icons.visibility_outlined
                                              : Icons.visibility_off_outlined,
                                          color: const Color(0xFF747B91),
                                        ),
                                      ),
                                    ),
                                    onSubmitted: (_) => _submit(),
                                  ),
                                ),
                                const SizedBox(height: 8),
                                CheckboxListTile(
                                  value: _rememberMe,
                                  contentPadding: EdgeInsets.zero,
                                  visualDensity: VisualDensity.compact,
                                  title: const Text(
                                    'Remember me',
                                    style: TextStyle(fontSize: 14),
                                  ),
                                  controlAffinity:
                                      ListTileControlAffinity.leading,
                                  onChanged: (value) {
                                    setState(() => _rememberMe = value ?? true);
                                  },
                                ),
                                if (_error.isNotEmpty) ...[
                                  const SizedBox(height: 4),
                                  Text(
                                    _error,
                                    textAlign: TextAlign.center,
                                    style: const TextStyle(
                                      color: Color(0xFFD83434),
                                      fontSize: 13,
                                      fontWeight: FontWeight.w500,
                                    ),
                                  ),
                                ],
                                const SizedBox(height: 12),
                                BrandButton(
                                  label: 'Login to Dashboard',
                                  onPressed: _loading ? null : _submit,
                                  loading: _loading,
                                ),
                                const SizedBox(height: 12),
                                const Text(
                                  'Forgot Password?',
                                  style: TextStyle(
                                    color: Color(0xFF5B6078),
                                    fontWeight: FontWeight.w500,
                                  ),
                                ),
                                const SizedBox(height: 4),
                                Text(
                                  'v1.0.0  •  ${AppConfig.appEnv}',
                                  style: TextStyle(
                                    color: const Color(0xFF6C7188),
                                    fontSize: isTablet ? 14 : 12,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                        SizedBox(height: isTablet ? 18 : 14),
                        Text(
                          '© DriveSphere Technologies',
                          style: TextStyle(
                            fontSize: footerSize,
                            color: const Color(0xFF6C7188),
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ),
        );
      },
    );
  }
}
