import 'package:flutter/material.dart';
import 'screens/login_screen.dart';
import 'screens/home_screen.dart';
import 'services/api_client.dart';

void main() => runApp(const PetroNexaApp());

class PetroNexaApp extends StatelessWidget {
  const PetroNexaApp({super.key});
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'PetroNexa',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(useMaterial3: true, brightness: Brightness.dark, scaffoldBackgroundColor: const Color(0xFF07111F), colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFFF2A900), brightness: Brightness.dark)),
      home: const LoginScreen(),
    );
  }
}
