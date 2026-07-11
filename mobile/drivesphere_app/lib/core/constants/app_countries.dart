import 'package:flutter/material.dart';

class CountryConfig {
  final String name;
  final String arabicName;
  final String flag;
  final String currencyCode;
  final Locale locale;
  final List<String> cities;
  final double centerLat;
  final double centerLng;

  const CountryConfig({
    required this.name,
    required this.arabicName,
    required this.flag,
    required this.currencyCode,
    required this.locale,
    required this.cities,
    required this.centerLat,
    required this.centerLng,
  });
}

class AppCountries {
  static const List<CountryConfig> supported = [
    CountryConfig(
      name: 'Oman',
      arabicName: 'عُمان',
      flag: '🇴🇲',
      currencyCode: 'OMR',
      locale: Locale('en'),
      cities: ['Muscat', 'Salalah', 'Sohar', 'Nizwa'],
      centerLat: 23.5880,
      centerLng: 58.3829,
    ),
    CountryConfig(
      name: 'United Arab Emirates',
      arabicName: 'الإمارات',
      flag: '🇦🇪',
      currencyCode: 'AED',
      locale: Locale('en'),
      cities: ['Dubai', 'Abu Dhabi', 'Sharjah', 'Ajman'],
      centerLat: 25.2048,
      centerLng: 55.2708,
    ),
    CountryConfig(
      name: 'Saudi Arabia',
      arabicName: 'السعودية',
      flag: '🇸🇦',
      currencyCode: 'SAR',
      locale: Locale('ar'),
      cities: ['Riyadh', 'Jeddah', 'Dammam', 'Madinah'],
      centerLat: 24.7136,
      centerLng: 46.6753,
    ),
    CountryConfig(
      name: 'Qatar',
      arabicName: 'قطر',
      flag: '🇶🇦',
      currencyCode: 'QAR',
      locale: Locale('ar'),
      cities: ['Doha', 'Al Wakrah', 'Lusail'],
      centerLat: 25.2854,
      centerLng: 51.5310,
    ),
    CountryConfig(
      name: 'Kuwait',
      arabicName: 'الكويت',
      flag: '🇰🇼',
      currencyCode: 'KWD',
      locale: Locale('ar'),
      cities: ['Kuwait City', 'Hawally', 'Salmiya'],
      centerLat: 29.3759,
      centerLng: 47.9774,
    ),
    CountryConfig(
      name: 'Bahrain',
      arabicName: 'البحرين',
      flag: '🇧🇭',
      currencyCode: 'BHD',
      locale: Locale('ar'),
      cities: ['Manama', 'Muharraq', 'Riffa'],
      centerLat: 26.2235,
      centerLng: 50.5876,
    ),
  ];

  static CountryConfig byName(String? name) {
    return supported.firstWhere(
      (e) => e.name == name,
      orElse: () => supported.first,
    );
  }
}