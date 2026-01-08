<?php /*

JellyChat Integration Plugin for Composr CMS
Provides seamless integration between Composr and Jellyfin JellyChat plugin

*/

if (!defined('HIPHOP_PHP')) exit();

/**
 * Hook for Composr startup to register JellyChat services
 */
function hook_startup_jellychat()
{
    // Register JellyChat API endpoints
    if (function_exists('register_api_endpoint')) {
        register_api_endpoint('jellychat_auth', 'jellychat_authenticate_user');
        register_api_endpoint('jellychat_profile', 'jellychat_get_user_profile');
        register_api_endpoint('jellychat_rooms', 'jellychat_get_chat_rooms');
        register_api_endpoint('jellychat_create_room', 'jellychat_create_chat_room');
    }
}

/**
 * Authentication endpoint for JellyChat
 */
function jellychat_authenticate_user()
{
    $username = post_param('username', '');
    $password = post_param('password', '');
    $is_guest = post_param_integer('is_guest', 0);
    
    header('Content-Type: application/json');
    
    if ($is_guest) {
        // Guest authentication
        $guest_name = $username ?: 'Guest_' . uniqid();
        
        echo json_encode([
            'success' => true,
            'user_type' => 'guest',
            'username' => $guest_name,
            'display_name' => $guest_name,
            'permissions' => ['chat_public'],
            'session_id' => 'guest_' . uniqid()
        ]);
        return;
    }
    
    // Regular user authentication
    if (empty($username) || empty($password)) {
        echo json_encode(['success' => false, 'error' => 'Username and password required']);
        return;
    }
    
    // Check if user exists and password is correct
    $member_id = $GLOBALS['FORUM_DB']->query_value_null_ok('f_members', 'id', ['m_username' => $username]);
    
    if (is_null($member_id)) {
        echo json_encode(['success' => false, 'error' => 'User not found']);
        return;
    }
    
    // Verify password (simplified - in real implementation, use proper Composr auth)
    $stored_password = $GLOBALS['FORUM_DB']->query_value('f_members', 'm_pass_hash_salted', ['id' => $member_id]);
    
    if (!ocf_check_password($password, $stored_password)) {
        echo json_encode(['success' => false, 'error' => 'Invalid password']);
        return;
    }
    
    // Get user details
    $user_data = $GLOBALS['FORUM_DB']->query_select_value('f_members', '*', ['id' => $member_id]);
    
    echo json_encode([
        'success' => true,
        'user_type' => 'member',
        'user_id' => $member_id,
        'username' => $user_data['m_username'],
        'display_name' => $user_data['m_username'],
        'email' => $user_data['m_email_address'],
        'join_date' => $user_data['m_join_time'],
        'permissions' => ['chat_public', 'chat_private', 'share_content'],
        'session_id' => 'member_' . $member_id . '_' . uniqid()
    ]);
}

/**
 * Get user profile for JellyChat
 */
function jellychat_get_user_profile()
{
    $username = get_param('username', '');
    
    header('Content-Type: application/json');
    
    if (empty($username)) {
        echo json_encode(['success' => false, 'error' => 'Username required']);
        return;
    }
    
    $member_id = $GLOBALS['FORUM_DB']->query_value_null_ok('f_members', 'id', ['m_username' => $username]);
    
    if (is_null($member_id)) {
        echo json_encode(['success' => false, 'error' => 'User not found']);
        return;
    }
    
    $user_data = $GLOBALS['FORUM_DB']->query_select_value('f_members', '*', ['id' => $member_id]);
    
    // Get avatar if available
    $avatar_url = '';
    if (function_exists('get_member_avatar')) {
        $avatar_url = get_member_avatar($member_id);
    }
    
    echo json_encode([
        'success' => true,
        'username' => $user_data['m_username'],
        'display_name' => $user_data['m_username'],
        'email' => $user_data['m_email_address'],
        'join_date' => date('c', $user_data['m_join_time']),
        'post_count' => $user_data['m_cache_num_posts'],
        'avatar_url' => $avatar_url,
        'is_active' => ($user_data['m_validated'] == 1),
        'last_visit' => date('c', $user_data['m_last_visit_time'])
    ]);
}

/**
 * Get available chat rooms
 */
function jellychat_get_chat_rooms()
{
    header('Content-Type: application/json');
    
    // Default chat rooms
    $chat_rooms = [
        [
            'id' => 'general',
            'name' => 'General Discussion',
            'description' => 'General chat for all users',
            'is_public' => true,
            'max_users' => 100,
            'current_users' => 0
        ],
        [
            'id' => 'support',
            'name' => 'Technical Support',
            'description' => 'Get help and technical support',
            'is_public' => true,
            'max_users' => 50,
            'current_users' => 0
        ]
    ];
    
    // Check for custom chat rooms in database
    if (function_exists('get_value') && table_exists('chat_rooms')) {
        $custom_rooms = $GLOBALS['SITE_DB']->query_select('chat_rooms', '*', ['is_active' => 1]);
        
        foreach ($custom_rooms as $room) {
            $chat_rooms[] = [
                'id' => 'custom_' . $room['id'],
                'name' => $room['room_name'],
                'description' => $room['room_description'],
                'is_public' => ($room['is_public'] == 1),
                'max_users' => $room['max_users'],
                'current_users' => 0 // Would need real-time tracking
            ];
        }
    }
    
    echo json_encode(['success' => true, 'rooms' => $chat_rooms]);
}

/**
 * Create a new chat room
 */
function jellychat_create_chat_room()
{
    $room_name = post_param('room_name', '');
    $room_description = post_param('room_description', '');
    $is_public = post_param_integer('is_public', 1);
    $max_users = post_param_integer('max_users', 50);
    
    header('Content-Type: application/json');
    
    if (empty($room_name)) {
        echo json_encode(['success' => false, 'error' => 'Room name required']);
        return;
    }
    
    // Check permissions (admin only for creating rooms)
    if (!has_actual_page_access(get_member(), 'admin_zone')) {
        echo json_encode(['success' => false, 'error' => 'Permission denied']);
        return;
    }
    
    // Create chat room record
    $room_id = 'room_' . uniqid();
    
    // If chat_rooms table exists, save to database
    if (table_exists('chat_rooms')) {
        $GLOBALS['SITE_DB']->query_insert('chat_rooms', [
            'room_id' => $room_id,
            'room_name' => $room_name,
            'room_description' => $room_description,
            'is_public' => $is_public,
            'max_users' => $max_users,
            'created_by' => get_member(),
            'created_time' => time(),
            'is_active' => 1
        ]);
    }
    
    echo json_encode([
        'success' => true,
        'room_id' => $room_id,
        'message' => 'Chat room created successfully'
    ]);
}

/**
 * Hook for user login to notify JellyChat
 */
function hook_post_login_jellychat($member_id)
{
    // Notify JellyChat of user login if configured
    $jellyfin_servers = get_value('jellychat_servers', '');
    
    if (!empty($jellyfin_servers)) {
        $servers = explode(',', $jellyfin_servers);
        
        foreach ($servers as $server) {
            $server = trim($server);
            if (!empty($server)) {
                // Send async notification to JellyChat
                jellychat_notify_user_status($server, $member_id, 'online');
            }
        }
    }
}

/**
 * Notify JellyChat of user status changes
 */
function jellychat_notify_user_status($jellyfin_server, $member_id, $status)
{
    $username = $GLOBALS['FORUM_DB']->query_value_null_ok('f_members', 'm_username', ['id' => $member_id]);
    
    if (!$username) return;
    
    $data = [
        'domain' => get_base_url(),
        'username' => $username,
        'status' => $status,
        'timestamp' => time()
    ];
    
    // Send async HTTP request to JellyChat
    $url = rtrim($jellyfin_server, '/') . '/jellychat/composr/user-status';
    
    // Use curl if available, otherwise skip
    if (function_exists('curl_init')) {
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, $url);
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
        curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
        curl_setopt($ch, CURLOPT_TIMEOUT, 5);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_exec($ch);
        curl_close($ch);
    }
}

/**
 * Create database table for chat rooms if needed
 */
function jellychat_create_tables()
{
    if (!table_exists('chat_rooms')) {
        $GLOBALS['SITE_DB']->query('
            CREATE TABLE ' . get_table_prefix() . 'chat_rooms (
                id INT AUTO_INCREMENT PRIMARY KEY,
                room_id VARCHAR(50) UNIQUE NOT NULL,
                room_name VARCHAR(100) NOT NULL,
                room_description TEXT,
                is_public TINYINT(1) DEFAULT 1,
                max_users INT DEFAULT 50,
                created_by INT,
                created_time INT,
                is_active TINYINT(1) DEFAULT 1,
                INDEX(room_id),
                INDEX(is_public),
                INDEX(is_active)
            )
        ');
    }
}

// Auto-create tables on first load
if (function_exists('table_exists')) {
    jellychat_create_tables();
}

?>