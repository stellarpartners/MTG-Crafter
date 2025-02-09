@group(0) @binding(0) var<storage, read> deck_array: array<u32>;
@group(0) @binding(1) var<storage, read> mana_costs: array<u32>;
@group(0) @binding(2) var<storage, read> lands_mask: array<u32>;
@group(0) @binding(3) var<storage, read_write> results: array<u32>;

@compute @workgroup_size(256)
fn simulate_hands(@builtin(global_invocation_id) global_id: vec3<u32>) {
    let thread_id = global_id.x;
    if (thread_id >= arrayLength(&results)) {
        return;
    }
    
    // Initialize mana tracking
    var available_mana: u32 = 0;
    var lands_played: u32 = 0;
    
    // Simulate drawing 7 cards for opening hand
    var lands_in_hand: array<u32, 7>;
    for (var i = 0u; i < 7u; i++) {
        if (lands_mask[i] != 0) {
            lands_in_hand[i] = 1;
            lands_played += 1;
            available_mana += 1;
        }
    }
    
    // Track when each card is first castable
    for (var turn = 1u; turn <= 10u; turn++) {
        // Add mana for turn's land drop
        if (turn > 1 && lands_played < turn) {
            available_mana += 1;
            lands_played += 1;
        }
        
        // Try to cast each card
        for (var card_idx = 0u; card_idx < arrayLength(&mana_costs); card_idx++) {
            let result_idx = thread_id * arrayLength(&mana_costs) + card_idx;
            if (results[result_idx] == 0 && available_mana >= mana_costs[card_idx]) {
                results[result_idx] = turn;
            }
        }
    }
} 