import 'package:flutter/material.dart';
import 'config.dart';
import 'screens/login_screen.dart';
import 'screens/home_screen.dart';
import 'services/api_client.dart';

void main() => runApp(const PetroNexaApp());

class PetroNexaApp extends StatelessWidget {
  const PetroNexaApp({super.key});

  @override
  Widget build(BuildContext context) {
    const gold = Color(0xFFF2A900);
    return MaterialApp(
      title: 'PetroNexa',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        brightness: Brightness.dark,
        scaffoldBackgroundColor: const Color(0xFF07111F),
        colorScheme: ColorScheme.fromSeed(seedColor: gold, brightness: Brightness.dark),
        inputDecorationTheme: const InputDecorationTheme(
          border: OutlineInputBorder(),
          filled: true,
        ),
      ),
      home: const StartupScreen(),
    );
  }
}

class StartupScreen extends StatefulWidget {
  const StartupScreen({super.key});
  @override State<StartupScreen> createState() => _StartupScreenState();
}

class _StartupScreenState extends State<StartupScreen> {
  final api = ApiClient();

  @override
  void initState() {
    super.initState();
    _open();
  }

  Future<void> _open() async {
    if (!AppConfig.isConfigured) {
      if (mounted) Navigator.pushReplacement(
        context, MaterialPageRoute(builder: (_) => const LoginScreen()),
      );
      return;
    }
    try {
      if (await api.hasSession()) {
        await api.me();
        if (mounted) Navigator.pushReplacement(
          context, MaterialPageRoute(builder: (_) => HomeScreen(api: api)),
        );
        return;
      }
    } catch (_) {
      await api.logout();
    }
    if (mounted) Navigator.pushReplacement(
      context, MaterialPageRoute(builder: (_) => const LoginScreen()),
    );
  }

  @override
  Widget build(BuildContext context) => const Scaffold(
    body: Center(child: CircularProgressIndicator()),
  );
}
