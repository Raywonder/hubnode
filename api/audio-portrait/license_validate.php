<?php
/**
 * Audio Portrait License Validation API
 * Standalone validation endpoint for WHMCS integration
 */

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

// Handle preflight OPTIONS request
if ($_SERVER['REQUEST_METHOD'] == 'OPTIONS') {
    exit(0);
}

// WHMCS database configuration
$db_host = 'localhost';
$db_name = 'devinecr_whmcs';
$db_user = 'devinecr_whmcs';
$db_pass = 'Tw3ntyt!m3s.';

try {
    $pdo = new PDO("mysql:host={$db_host};dbname={$db_name}", $db_user, $db_pass);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
} catch (PDOException $e) {
    http_response_code(500);
    echo json_encode(['status' => 'error', 'message' => 'Database connection failed']);
    exit;
}

// Get parameters
$license_key = $_GET['license_key'] ?? $_POST['license_key'] ?? '';
$app_version = $_GET['app_version'] ?? $_POST['app_version'] ?? '';
$platform = $_GET['platform'] ?? $_POST['platform'] ?? 'unknown';
$machine_id = $_GET['machine_id'] ?? $_POST['machine_id'] ?? '';

// Log the validation attempt
error_log("Audio Portrait License Validation: key={$license_key}, version={$app_version}, platform={$platform}");

if (!$license_key) {
    http_response_code(400);
    echo json_encode([
        'status' => 'error',
        'message' => 'License key is required',
        'valid' => false
    ]);
    exit;
}

try {
    // Query license from UFM License Manager database
    $stmt = $pdo->prepare("SELECT * FROM mod_ufm_licenses WHERE license_key = ? AND product = 'AUDIO_PORTRAIT' LIMIT 1");
    $stmt->execute([$license_key]);
    $license = $stmt->fetch(PDO::FETCH_ASSOC);
    
    if (!$license) {
        // Log failed validation in UFM validation table
        $log_stmt = $pdo->prepare("INSERT INTO mod_ufm_license_validations (license_key, fingerprint, ip_address, user_agent, product, version, platform, result, request_data, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NOW())");
        $log_stmt->execute([$license_key, $machine_id, $_SERVER['REMOTE_ADDR'], $_SERVER['HTTP_USER_AGENT'] ?? '', 'AUDIO_PORTRAIT', $app_version, $platform, 'invalid', json_encode(['reason' => 'license_not_found'])]);
        
        echo json_encode([
            'status' => 'invalid',
            'message' => 'License key not found',
            'valid' => false
        ]);
        exit;
    }
    
    // Check license status
    if ($license['status'] !== 'active') {
        echo json_encode([
            'status' => 'inactive',
            'message' => "License is {$license['status']}",
            'valid' => false,
            'license_status' => $license['status']
        ]);
        exit;
    }
    
    // Check expiry date
    $expired = false;
    if ($license['expires_at'] && strtotime($license['expires_at']) < time()) {
        $expired = true;
        
        // Auto-update expired licenses to expired status
        $update_stmt = $pdo->prepare("UPDATE mod_ufm_licenses SET status = 'expired' WHERE id = ?");
        $update_stmt->execute([$license['id']]);
        
        echo json_encode([
            'status' => 'expired',
            'message' => 'License has expired',
            'valid' => false,
            'expiry_date' => $license['expires_at']
        ]);
        exit;
    }
    
    // Parse license limitations
    $limitations = json_decode($license['limitations'], true) ?? [];
    $version_limit = $limitations['version_limit'] ?? 'unlimited';
    
    // Check version compatibility
    $version_allowed = true;
    if ($version_limit !== 'unlimited' && !empty($version_limit) && !empty($app_version)) {
        // Simple version matching (can be enhanced)
        $version_pattern = str_replace('x', '\d+', $version_limit);
        if (!preg_match("/^{$version_pattern}/", $app_version)) {
            $version_allowed = false;
        }
    }
    
    // Get client information
    $client_stmt = $pdo->prepare("SELECT firstname, lastname, email FROM tblclients WHERE id = ? LIMIT 1");
    $client_stmt->execute([$license['client_id']]);
    $client = $client_stmt->fetch(PDO::FETCH_ASSOC);
    
    // Log successful validation
    $log_stmt = $pdo->prepare("INSERT INTO mod_ufm_license_validations (license_key, fingerprint, ip_address, user_agent, product, version, platform, result, request_data, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NOW())");
    $log_stmt->execute([$license_key, $machine_id, $_SERVER['REMOTE_ADDR'], $_SERVER['HTTP_USER_AGENT'] ?? '', 'AUDIO_PORTRAIT', $app_version, $platform, 'valid', json_encode(['version_allowed' => $version_allowed])]);
    
    // Update license last validation
    $update_stmt = $pdo->prepare("UPDATE mod_ufm_licenses SET last_validated = NOW(), validation_count = validation_count + 1 WHERE id = ?");
    $update_stmt->execute([$license['id']]);
    
    // Parse features
    $features = json_decode($license['features'], true) ?? [];
    
    // Return validation response
    echo json_encode([
        'status' => 'valid',
        'message' => 'License is valid and active',
        'valid' => true,
        'license_info' => [
            'type' => $license['license_type'],
            'version_limit' => $version_limit,
            'created_date' => $license['issued_at'],
            'expiry_date' => $license['expires_at'],
            'validation_count' => $license['validation_count'] + 1,
            'features' => $features,
            'limitations' => $limitations
        ],
        'client_info' => [
            'name' => ($client['firstname'] ?? '') . ' ' . ($client['lastname'] ?? ''),
            'email' => $client['email'] ?? ''
        ],
        'version_allowed' => $version_allowed,
        'features' => [
            'unlimited_versions' => $version_limit === 'unlimited',
            'support_included' => $license['license_type'] === 'enterprise',
            'commercial_use' => in_array($license['license_type'], ['professional', 'enterprise']),
            'export_formats' => $limitations['export_formats'] ?? -1,
            'custom_features' => $limitations['custom_features'] ?? false
        ]
    ]);
    
} catch (PDOException $e) {
    error_log("Audio Portrait License Validation Error: " . $e->getMessage());
    http_response_code(500);
    echo json_encode([
        'status' => 'error',
        'message' => 'Validation service temporarily unavailable',
        'valid' => false
    ]);
}

?>