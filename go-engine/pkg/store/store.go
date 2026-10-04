// Package store defines persistence boundaries. The engine and rule-management
// services depend on these interfaces, never on JSON files or a database driver.
package store

import (
	"context"
	"errors"

	"github.com/shubbhang351/shield-and-sword/go-engine/pkg/models"
)

var ErrNotFound = errors.New("store: record not found")

type RuleQuery struct {
	EventType       models.EventType
	Ruleset         string
	MerchantID      string
	IncludeInactive bool
}

type ParameterQuery struct {
	EventType models.EventType
}

type RuleStore interface {
	ListRules(context.Context, RuleQuery) ([]models.Rule, error)
	GetRule(context.Context, string) (models.Rule, error)
	CreateRule(context.Context, models.Rule) error
	UpdateRule(context.Context, models.Rule) error
	DeleteRule(context.Context, string) error
}

type ParameterStore interface {
	ListParameters(context.Context, ParameterQuery) ([]models.ParameterDefinition, error)
	GetParameter(context.Context, string) (models.ParameterDefinition, error)
	CreateParameter(context.Context, models.ParameterDefinition) error
	UpdateParameter(context.Context, models.ParameterDefinition) error
	DeleteParameter(context.Context, string) error
}
