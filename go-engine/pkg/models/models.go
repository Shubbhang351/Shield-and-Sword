// Package models contains transport-neutral types shared by the rule engine,
// parameter registry, and storage adapters.
package models

import "time"

type EventType string

const (
	EventTransaction EventType = "transaction"
	EventEmail       EventType = "email"
	EventSecurity    EventType = "security_event"
	EventPayout      EventType = "payout"
	EventRefund      EventType = "refund"

	SharedMerchantID = "100000Razorpay"
)

type Action string

const (
	ActionBlock     Action = "BLOCK"
	ActionReview    Action = "REVIEW"
	ActionAllow     Action = "ALLOW"
	ActionWhitelist Action = "WHITELIST"
)

// Precedence follows the reference's action ordering for the V1 action set.
// A higher value wins after all matching rules have been evaluated.
func (a Action) Precedence() int {
	switch a {
	case ActionWhitelist:
		return 4
	case ActionBlock:
		return 3
	case ActionReview:
		return 2
	case ActionAllow:
		return 1
	default:
		return 0
	}
}

type RuleType string

const (
	RuleTypeAction RuleType = "action"
	RuleTypeWeight RuleType = "weight"
)

type ValueType string

const (
	ValueString     ValueType = "string"
	ValueNumber     ValueType = "number"
	ValueInteger    ValueType = "integer"
	ValueBoolean    ValueType = "boolean"
	ValueStringList ValueType = "string_list"
	ValueNumberList ValueType = "number_list"
)

type ParameterSource string

const (
	ParameterInput   ParameterSource = "input"
	ParameterDerived ParameterSource = "derived"
	ParameterMemory  ParameterSource = "memory"
	ParameterRedis   ParameterSource = "redis"
)

// ParameterDefinition is a typed, approved name that a rule expression may
// reference. Resolver names map to code-registered functions; JSON never stores
// executable code.
type ParameterDefinition struct {
	Name             string          `json:"name"`
	Type             ValueType       `json:"type"`
	Source           ParameterSource `json:"source"`
	EventTypes       []EventType     `json:"event_types"`
	InputKeys        []string        `json:"input_keys,omitempty"`
	Resolver         string          `json:"resolver,omitempty"`
	RedisKeyTemplate string          `json:"redis_key_template,omitempty"`
	Window           string          `json:"window,omitempty"`
	Required         bool            `json:"required"`
	ShouldLogValue   bool            `json:"should_log_value"`
}

type Rule struct {
	ID                    string      `json:"id"`
	RuleCode              string      `json:"rule_code"`
	RuleNumber            uint64      `json:"rule_number,omitempty"`
	Name                  string      `json:"name"`
	Description           string      `json:"description,omitempty"`
	Expression            string      `json:"expression"`
	EventTypes            []EventType `json:"event_types"`
	Ruleset               string      `json:"ruleset"`
	MerchantID            string      `json:"merchant_id,omitempty"`
	IsActive              bool        `json:"is_active"`
	Type                  RuleType    `json:"type"`
	Action                Action      `json:"action,omitempty"`
	OnParameterError      Action      `json:"on_parameter_error,omitempty"`
	Weight                float64     `json:"weight,omitempty"`
	Mode                  string      `json:"mode,omitempty"`
	CaseCreationFlag      bool        `json:"case_creation_flag,omitempty"`
	AutoBlockFlag         bool        `json:"auto_block_flag,omitempty"`
	OverrideWhitelistFlag bool        `json:"override_whitelist_flag,omitempty"`
	CreatedAt             time.Time   `json:"created_at,omitempty"`
	UpdatedAt             time.Time   `json:"updated_at,omitempty"`
}

// EvaluationRequest is the common envelope for payment, email, and security
// events. Domain-specific data remains in Input and is validated by the
// parameter catalog for the selected EventType.
type EvaluationRequest struct {
	Rulesets             []string       `json:"rulesets,omitempty"`
	SkipDefaultExecution bool           `json:"skip_default_execution,omitempty"`
	MerchantID           string         `json:"merchant_id,omitempty"`
	EntityID             string         `json:"entity_id"`
	EntityType           EventType      `json:"entity_type"`
	Input                map[string]any `json:"input"`
	OccurredAt           time.Time      `json:"occurred_at,omitempty"`
	TestMode             bool           `json:"test_mode,omitempty"`
}

type TriggeredRule struct {
	ID          string  `json:"id"`
	RuleCode    string  `json:"rule_code"`
	RuleName    string  `json:"rule_name"`
	Description string  `json:"rule_description,omitempty"`
	Action      Action  `json:"action"`
	Weight      float64 `json:"weight,omitempty"`
}

type EvaluationResult struct {
	Action              Action                     `json:"action"`
	TriggeredRuleWeight float64                    `json:"triggered_rule_weight,omitempty"`
	MaxRuleWeight       float64                    `json:"max_rule_weight,omitempty"`
	TriggeredRules      map[Action][]TriggeredRule `json:"triggered_rules"`
}
