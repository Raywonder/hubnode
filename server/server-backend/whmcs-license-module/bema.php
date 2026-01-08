<?php
/**
 * BEMA - WHMCS License Module
 * Version: 1.0.0
 * 
 * This module handles license validation for BEMA
 * Path: /home/devinecr/public_html/modules/servers/bema/bema.php
 */

use WHMCS\Database\Capsule;

if (!defined("WHMCS")) {
    die("This file cannot be accessed directly");
}

/**
 * Module meta data
 */
function simplemediaplayer_MetaData() {
    return array(
        'DisplayName' => 'BEMA License',
        'APIVersion' => '1.1',
        'RequiresServer' => false,
        'DefaultSSLPort' => 443,
    );
}

/**
 * Configuration array for module settings
 */
function simplemediaplayer_ConfigOptions() {
    return array(
        'License Type' => array(
            'Type' => 'dropdown',
            'Options' => array(
                'personal' => 'Personal License',
                'commercial' => 'Commercial License',
                'enterprise' => 'Enterprise License',
            ),
            'Default' => 'personal',
        ),
        'Max Installations' => array(
            'Type' => 'text',
            'Size' => '5',
            'Default' => '1',
            'Description' => 'Maximum number of installations allowed',
        ),
        'Features' => array(
            'Type' => 'dropdown',
            'Options' => array(
                'basic' => 'Basic Features',
                'advanced' => 'Advanced Features (Server API)',
                'pro' => 'Professional Features (All)',
            ),
            'Default' => 'basic',
        ),
        'License Duration' => array(
            'Type' => 'dropdown',
            'Options' => array(
                'lifetime' => 'Lifetime',
                '365' => '1 Year',
                '180' => '6 Months',
                '90' => '3 Months',
                '30' => '1 Month',
            ),
            'Default' => 'lifetime',
        ),
    );
}

/**
 * Create account on service activation
 */
function simplemediaplayer_CreateAccount($params) {
    try {
        // Generate unique license key
        $licenseKey = generateLicenseKey($params);
        
        // Store license in database
        $result = storeLicense($params, $licenseKey);
        
        if ($result['success']) {
            return 'success';
        } else {
            return $result['error'];
        }
        
    } catch (Exception $e) {
        logActivity("BEMA License Creation Failed: " . $e->getMessage());
        return $e->getMessage();
    }
}

/**
 * Suspend account
 */
function simplemediaplayer_SuspendAccount($params) {
    try {
        $licenseKey = getLicenseKey($params);
        if ($licenseKey) {
            updateLicenseStatus($licenseKey, 'suspended');
            return 'success';
        }
        return 'License not found';
    } catch (Exception $e) {
        return $e->getMessage();
    }
}

/**
 * Unsuspend account
 */
function simplemediaplayer_UnsuspendAccount($params) {
    try {
        $licenseKey = getLicenseKey($params);
        if ($licenseKey) {
            updateLicenseStatus($licenseKey, 'active');
            return 'success';
        }
        return 'License not found';
    } catch (Exception $e) {
        return $e->getMessage();
    }
}

/**
 * Terminate account
 */
function simplemediaplayer_TerminateAccount($params) {
    try {
        $licenseKey = getLicenseKey($params);
        if ($licenseKey) {
            updateLicenseStatus($licenseKey, 'terminated');
            return 'success';
        }
        return 'License not found';
    } catch (Exception $e) {
        return $e->getMessage();
    }
}

/**
 * Test connection to license server
 */
function simplemediaplayer_TestConnection($params) {
    try {
        // Test API endpoint
        $apiUrl = 'https://raywonderis.me/api/health';
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, $apiUrl);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_TIMEOUT, 10);
        curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
        
        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        
        if ($httpCode === 200) {
            return array(
                'success' => true,
                'error' => ''
            );
        } else {
            return array(
                'success' => false,
                'error' => 'License server unreachable (HTTP ' . $httpCode . ')'
            );
        }
        
    } catch (Exception $e) {
        return array(
            'success' => false,
            'error' => $e->getMessage()
        );
    }
}

/**
 * Generate unique license key
 */
function generateLicenseKey($params) {
    $prefix = 'BEMA'; // BEMA
    $type = strtoupper(substr($params['configoption1'], 0, 1)); // P, C, E
    $timestamp = time();
    $random = strtoupper(bin2hex(random_bytes(4)));
    $checksum = substr(md5($params['serviceid'] . $timestamp), 0, 4);
    
    return $prefix . '-' . $type . $random . '-' . strtoupper(dechex($timestamp)) . '-' . strtoupper($checksum);
}

/**
 * Store license in database
 */
function storeLicense($params, $licenseKey) {
    try {
        // Create licenses table if not exists
        createLicensesTable();
        
        // Calculate expiry date
        $duration = $params['configoption4'];
        if ($duration === 'lifetime') {
            $expiryDate = null;
        } else {
            $expiryDate = date('Y-m-d H:i:s', strtotime('+' . $duration . ' days'));
        }
        
        // Get feature list based on selected features
        $features = getFeaturesArray($params['configoption3']);
        
        // Insert license record
        Capsule::table('mod_simplemediaplayer_licenses')->insert([
            'service_id' => $params['serviceid'],
            'user_id' => $params['userid'],
            'license_key' => $licenseKey,
            'license_type' => $params['configoption1'],
            'max_installations' => $params['configoption2'],
            'features' => json_encode($features),
            'status' => 'active',
            'created_at' => date('Y-m-d H:i:s'),
            'expires_at' => $expiryDate,
            'installations' => 0
        ]);
        
        // Store license key in service custom fields or notes
        Capsule::table('tblhosting')
            ->where('id', $params['serviceid'])
            ->update(['notes' => "License Key: " . $licenseKey]);
        
        return array('success' => true);
        
    } catch (Exception $e) {
        return array(
            'success' => false,
            'error' => $e->getMessage()
        );
    }
}

/**
 * Get license key for service
 */
function getLicenseKey($params) {
    try {
        $license = Capsule::table('mod_simplemediaplayer_licenses')
            ->where('service_id', $params['serviceid'])
            ->first();
            
        return $license ? $license->license_key : null;
    } catch (Exception $e) {
        return null;
    }
}

/**
 * Update license status
 */
function updateLicenseStatus($licenseKey, $status) {
    try {
        return Capsule::table('mod_simplemediaplayer_licenses')
            ->where('license_key', $licenseKey)
            ->update(['status' => $status]);
    } catch (Exception $e) {
        return false;
    }
}

/**
 * Create licenses table
 */
function createLicensesTable() {
    try {
        if (!Capsule::schema()->hasTable('mod_simplemediaplayer_licenses')) {
            Capsule::schema()->create('mod_simplemediaplayer_licenses', function ($table) {
                $table->increments('id');
                $table->integer('service_id');
                $table->integer('user_id');
                $table->string('license_key', 100)->unique();
                $table->enum('license_type', ['personal', 'commercial', 'enterprise']);
                $table->integer('max_installations')->default(1);
                $table->text('features')->nullable();
                $table->enum('status', ['active', 'suspended', 'terminated'])->default('active');
                $table->timestamp('created_at');
                $table->timestamp('expires_at')->nullable();
                $table->integer('installations')->default(0);
                $table->timestamp('last_validation')->nullable();
                $table->text('validation_data')->nullable();
                
                $table->index('service_id');
                $table->index('license_key');
                $table->index('status');
            });
        }
    } catch (Exception $e) {
        logActivity("BEMA: Failed to create licenses table - " . $e->getMessage());
    }
}

/**
 * Get features array based on feature level
 */
function getFeaturesArray($featureLevel) {
    $baseFeatures = ['media-playback'];
    
    switch ($featureLevel) {
        case 'advanced':
            return array_merge($baseFeatures, ['server-api', 'auto-updates']);
        case 'pro':
            return array_merge($baseFeatures, ['server-api', 'auto-updates', 'hubnode', 'socket-server', 'advanced-ui']);
        default:
            return $baseFeatures;
    }
}

/**
 * Client area output
 */
function simplemediaplayer_ClientArea($params) {
    $licenseKey = getLicenseKey($params);
    
    $license = null;
    if ($licenseKey) {
        $license = Capsule::table('mod_simplemediaplayer_licenses')
            ->where('license_key', $licenseKey)
            ->first();
    }
    
    $templateVars = array(
        'license_key' => $licenseKey,
        'license' => $license,
        'download_url' => 'https://raywonderis.me/downloads/mediaplayer/',
        'api_status_url' => 'https://raywonderis.me/api/health',
    );
    
    return array(
        'templatefile' => 'clientarea',
        'vars' => $templateVars,
    );
}

/**
 * Admin area output
 */
function simplemediaplayer_AdminCustomButtonArray() {
    return array(
        'Regenerate License' => 'regenerateLicense',
        'View Installations' => 'viewInstallations',
        'Reset Installations' => 'resetInstallations',
    );
}

/**
 * Regenerate license key
 */
function simplemediaplayer_regenerateLicense($params) {
    try {
        $oldLicenseKey = getLicenseKey($params);
        $newLicenseKey = generateLicenseKey($params);
        
        if ($oldLicenseKey) {
            Capsule::table('mod_simplemediaplayer_licenses')
                ->where('license_key', $oldLicenseKey)
                ->update(['license_key' => $newLicenseKey]);
                
            Capsule::table('tblhosting')
                ->where('id', $params['serviceid'])
                ->update(['notes' => "License Key: " . $newLicenseKey]);
        }
        
        return 'success';
    } catch (Exception $e) {
        return $e->getMessage();
    }
}

/**
 * View installations
 */
function simplemediaplayer_viewInstallations($params) {
    try {
        $licenseKey = getLicenseKey($params);
        if ($licenseKey) {
            $license = Capsule::table('mod_simplemediaplayer_licenses')
                ->where('license_key', $licenseKey)
                ->first();
                
            if ($license) {
                return "Installations: " . $license->installations . "/" . $license->max_installations;
            }
        }
        return "No license found";
    } catch (Exception $e) {
        return $e->getMessage();
    }
}

/**
 * Reset installations count
 */
function simplemediaplayer_resetInstallations($params) {
    try {
        $licenseKey = getLicenseKey($params);
        if ($licenseKey) {
            Capsule::table('mod_simplemediaplayer_licenses')
                ->where('license_key', $licenseKey)
                ->update(['installations' => 0]);
            return 'success';
        }
        return "License not found";
    } catch (Exception $e) {
        return $e->getMessage();
    }
}