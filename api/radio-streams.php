<?php
/**
 * HubNode Radio Streams API
 * Provides streaming status and control for all radio streams
 */

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST');
header('Access-Control-Allow-Headers: Content-Type');

// Stream configurations
$streams = [
    'raywonder' => [
        'name' => 'Raywonder Radio',
        'url' => 'http://stream.raywonderis.me:8003/jellyfin-radio',
        'icecast_status' => 'http://64.20.46.178:8003/status-json.xsl',
        'now_playing_file' => '/home/dom/apps/jellyfin-now-playing.json',
        'queue_file' => '/home/dom/apps/jellyfin-queue.json',
        'type' => 'jellyfin',
        'description' => 'Audio described TV, movies, audiobooks and music'
    ],
    'tappedin' => [
        'name' => 'TappedIn.FM',
        'url' => 'http://stream.tappedin.fm:8004/tappedin-radio',
        'icecast_status' => 'http://64.20.46.178:8004/status-json.xsl',
        'now_playing_file' => '/home/tappedin/apps/tappedin-now-playing.json',
        'type' => 'podcast',
        'description' => 'Soundscapes, podcasts, and station IDs'
    ]
];

// Get Icecast status
function getIcecastStatus($url) {
    $data = @file_get_contents($url);
    if (!$data) {
        return null;
    }

    $json = json_decode($data, true);
    if (!isset($json['icestats']['source'])) {
        return null;
    }

    $source = $json['icestats']['source'];
    return [
        'active' => true,
        'listeners' => $source['listeners'] ?? 0,
        'listener_peak' => $source['listener_peak'] ?? 0,
        'bitrate' => $source['bitrate'] ?? 0,
        'server_type' => $source['server_type'] ?? 'unknown',
        'stream_start' => $source['stream_start'] ?? null,
        'stream_start_iso8601' => $source['stream_start_iso8601'] ?? null
    ];
}

// Get now playing info
function getNowPlaying($file) {
    if (!file_exists($file)) {
        return null;
    }

    $data = json_decode(file_get_contents($file), true);
    return $data ?? null;
}

// Get queue info
function getQueue($file) {
    if (!file_exists($file)) {
        return [];
    }

    $data = json_decode(file_get_contents($file), true);
    return $data ?? [];
}

// Handle GET requests - return all streams status
if ($_SERVER['REQUEST_METHOD'] === 'GET') {
    $stream_id = $_GET['stream'] ?? null;

    if ($stream_id && isset($streams[$stream_id])) {
        // Return single stream status
        $stream = $streams[$stream_id];
        $icecast = getIcecastStatus($stream['icecast_status']);
        $nowPlaying = isset($stream['now_playing_file']) ? getNowPlaying($stream['now_playing_file']) : null;
        $queue = isset($stream['queue_file']) ? getQueue($stream['queue_file']) : [];

        echo json_encode([
            'status' => 'success',
            'stream' => [
                'id' => $stream_id,
                'name' => $stream['name'],
                'url' => $stream['url'],
                'type' => $stream['type'],
                'description' => $stream['description'],
                'icecast' => $icecast,
                'now_playing' => $nowPlaying,
                'queue' => $queue,
                'queue_length' => count($queue)
            ]
        ]);
    } else {
        // Return all streams status
        $allStreams = [];

        foreach ($streams as $id => $stream) {
            $icecast = getIcecastStatus($stream['icecast_status']);
            $nowPlaying = isset($stream['now_playing_file']) ? getNowPlaying($stream['now_playing_file']) : null;
            $queue = isset($stream['queue_file']) ? getQueue($stream['queue_file']) : [];

            $allStreams[] = [
                'id' => $id,
                'name' => $stream['name'],
                'url' => $stream['url'],
                'type' => $stream['type'],
                'description' => $stream['description'],
                'active' => $icecast !== null,
                'listeners' => $icecast['listeners'] ?? 0,
                'now_playing' => $nowPlaying ? ($nowPlaying['track'] ?? 'Unknown') : null,
                'queue_length' => count($queue)
            ];
        }

        echo json_encode([
            'status' => 'success',
            'streams' => $allStreams,
            'total_streams' => count($allStreams),
            'active_streams' => count(array_filter($allStreams, fn($s) => $s['active']))
        ]);
    }
    exit;
}

// Handle POST requests - queue management
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $input = json_decode(file_get_contents('php://input'), true);
    $stream_id = $input['stream'] ?? null;
    $action = $input['action'] ?? '';

    if (!$stream_id || !isset($streams[$stream_id])) {
        echo json_encode([
            'status' => 'error',
            'message' => 'Invalid stream ID'
        ]);
        exit;
    }

    $stream = $streams[$stream_id];

    if (!isset($stream['queue_file'])) {
        echo json_encode([
            'status' => 'error',
            'message' => 'This stream does not support queuing'
        ]);
        exit;
    }

    $queueFile = $stream['queue_file'];

    // Load existing queue
    $queue = [];
    if (file_exists($queueFile)) {
        $queue = json_decode(file_get_contents($queueFile), true) ?: [];
    }

    switch ($action) {
        case 'add':
            $newItem = [
                'type' => $input['type'] ?? 'music',
                'count' => $input['count'] ?? 2,
                'with_intros' => $input['with_intros'] ?? true,
                'show' => $input['show'] ?? null,
                'season' => $input['season'] ?? null,
                'added_at' => time(),
                'added_via' => 'hubnode_api'
            ];

            $title = ucfirst($newItem['type']);
            if ($newItem['show']) {
                $title = $newItem['show'];
                if ($newItem['season']) {
                    $title .= ' - ' . $newItem['season'];
                }
            }
            $newItem['title'] = $title;

            $queue[] = $newItem;
            file_put_contents($queueFile, json_encode($queue, JSON_PRETTY_PRINT));

            echo json_encode([
                'status' => 'success',
                'message' => 'Added to ' . $stream['name'] . ' queue: ' . $title,
                'queue_length' => count($queue)
            ]);
            break;

        case 'remove':
            $index = $input['index'] ?? -1;
            if ($index >= 0 && $index < count($queue)) {
                $removed = array_splice($queue, $index, 1);
                file_put_contents($queueFile, json_encode($queue, JSON_PRETTY_PRINT));

                echo json_encode([
                    'status' => 'success',
                    'message' => 'Removed: ' . $removed[0]['title'],
                    'queue_length' => count($queue)
                ]);
            } else {
                echo json_encode([
                    'status' => 'error',
                    'message' => 'Invalid queue index'
                ]);
            }
            break;

        case 'clear':
            file_put_contents($queueFile, json_encode([], JSON_PRETTY_PRINT));
            echo json_encode([
                'status' => 'success',
                'message' => 'Queue cleared for ' . $stream['name']
            ]);
            break;

        default:
            echo json_encode([
                'status' => 'error',
                'message' => 'Unknown action: ' . $action
            ]);
    }
    exit;
}

echo json_encode([
    'status' => 'error',
    'message' => 'Method not allowed'
]);
