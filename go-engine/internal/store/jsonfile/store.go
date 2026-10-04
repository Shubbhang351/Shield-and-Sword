// Package jsonfile implements the storage contracts with local JSON files.
// It is a single-process V1 adapter; engine code only sees pkg/store interfaces.
package jsonfile

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"slices"
	"strings"
	"sync"

	"github.com/shubbhang351/shield-and-sword/go-engine/pkg/models"
	"github.com/shubbhang351/shield-and-sword/go-engine/pkg/store"
)

const fileVersion = 1

type Store struct {
	mu             sync.RWMutex
	rulesPath      string
	parametersPath string
}

type ruleFile struct {
	Version int           `json:"version"`
	Rules   []models.Rule `json:"rules"`
}

type parameterFile struct {
	Version    int                          `json:"version"`
	Parameters []models.ParameterDefinition `json:"parameters"`
}

func New(directory string) (*Store, error) {
	if strings.TrimSpace(directory) == "" {
		return nil, errors.New("jsonfile: directory is required")
	}
	if err := os.MkdirAll(directory, 0o750); err != nil {
		return nil, fmt.Errorf("jsonfile: create data directory: %w", err)
	}
	s := &Store{
		rulesPath:      filepath.Join(directory, "rules.json"),
		parametersPath: filepath.Join(directory, "parameters.json"),
	}
	if err := initializeFile(s.rulesPath, ruleFile{Version: fileVersion, Rules: []models.Rule{}}); err != nil {
		return nil, err
	}
	if err := initializeFile(s.parametersPath, parameterFile{
		Version: fileVersion, Parameters: []models.ParameterDefinition{},
	}); err != nil {
		return nil, err
	}
	return s, nil
}

func initializeFile[T any](path string, initial T) error {
	if _, err := os.Stat(path); err == nil {
		return nil
	} else if !errors.Is(err, os.ErrNotExist) {
		return fmt.Errorf("jsonfile: inspect %s: %w", path, err)
	}
	if err := writeJSONAtomic(path, initial); err != nil {
		return fmt.Errorf("jsonfile: initialize %s: %w", path, err)
	}
	return nil
}

func (s *Store) ListRules(ctx context.Context, query store.RuleQuery) ([]models.Rule, error) {
	if err := ctx.Err(); err != nil {
		return nil, err
	}
	s.mu.RLock()
	defer s.mu.RUnlock()

	catalog, err := readJSON[ruleFile](s.rulesPath)
	if err != nil {
		return nil, err
	}
	result := make([]models.Rule, 0, len(catalog.Rules))
	for _, rule := range catalog.Rules {
		if !query.IncludeInactive && !rule.IsActive {
			continue
		}
		if query.EventType != "" && !slices.Contains(rule.EventTypes, query.EventType) {
			continue
		}
		if query.Ruleset != "" && rule.Ruleset != query.Ruleset {
			continue
		}
		if query.MerchantID != "" && rule.MerchantID != "" &&
			rule.MerchantID != query.MerchantID && rule.MerchantID != models.SharedMerchantID {
			continue
		}
		result = append(result, rule)
	}
	return result, nil
}

func (s *Store) GetRule(ctx context.Context, id string) (models.Rule, error) {
	if err := ctx.Err(); err != nil {
		return models.Rule{}, err
	}
	s.mu.RLock()
	defer s.mu.RUnlock()

	catalog, err := readJSON[ruleFile](s.rulesPath)
	if err != nil {
		return models.Rule{}, err
	}
	for _, rule := range catalog.Rules {
		if rule.ID == id {
			return rule, nil
		}
	}
	return models.Rule{}, store.ErrNotFound
}

func (s *Store) CreateRule(ctx context.Context, rule models.Rule) error {
	if err := ctx.Err(); err != nil {
		return err
	}
	if strings.TrimSpace(rule.ID) == "" {
		return errors.New("jsonfile: rule ID is required")
	}
	s.mu.Lock()
	defer s.mu.Unlock()

	catalog, err := readJSON[ruleFile](s.rulesPath)
	if err != nil {
		return err
	}
	for _, existing := range catalog.Rules {
		if existing.ID == rule.ID {
			return fmt.Errorf("jsonfile: rule %q already exists", rule.ID)
		}
	}
	catalog.Rules = append(catalog.Rules, rule)
	return writeJSONAtomic(s.rulesPath, catalog)
}

func (s *Store) UpdateRule(ctx context.Context, rule models.Rule) error {
	if err := ctx.Err(); err != nil {
		return err
	}
	if strings.TrimSpace(rule.ID) == "" {
		return errors.New("jsonfile: rule ID is required")
	}
	s.mu.Lock()
	defer s.mu.Unlock()

	catalog, err := readJSON[ruleFile](s.rulesPath)
	if err != nil {
		return err
	}
	for i := range catalog.Rules {
		if catalog.Rules[i].ID == rule.ID {
			catalog.Rules[i] = rule
			return writeJSONAtomic(s.rulesPath, catalog)
		}
	}
	return store.ErrNotFound
}

func (s *Store) DeleteRule(ctx context.Context, id string) error {
	if err := ctx.Err(); err != nil {
		return err
	}
	s.mu.Lock()
	defer s.mu.Unlock()

	catalog, err := readJSON[ruleFile](s.rulesPath)
	if err != nil {
		return err
	}
	for i := range catalog.Rules {
		if catalog.Rules[i].ID == id {
			catalog.Rules = append(catalog.Rules[:i], catalog.Rules[i+1:]...)
			return writeJSONAtomic(s.rulesPath, catalog)
		}
	}
	return store.ErrNotFound
}

func (s *Store) ListParameters(ctx context.Context, query store.ParameterQuery) ([]models.ParameterDefinition, error) {
	if err := ctx.Err(); err != nil {
		return nil, err
	}
	s.mu.RLock()
	defer s.mu.RUnlock()

	catalog, err := readJSON[parameterFile](s.parametersPath)
	if err != nil {
		return nil, err
	}
	result := make([]models.ParameterDefinition, 0, len(catalog.Parameters))
	for _, parameter := range catalog.Parameters {
		if query.EventType != "" && !slices.Contains(parameter.EventTypes, query.EventType) {
			continue
		}
		result = append(result, parameter)
	}
	return result, nil
}

func (s *Store) GetParameter(ctx context.Context, name string) (models.ParameterDefinition, error) {
	if err := ctx.Err(); err != nil {
		return models.ParameterDefinition{}, err
	}
	s.mu.RLock()
	defer s.mu.RUnlock()

	catalog, err := readJSON[parameterFile](s.parametersPath)
	if err != nil {
		return models.ParameterDefinition{}, err
	}
	for _, parameter := range catalog.Parameters {
		if parameter.Name == name {
			return parameter, nil
		}
	}
	return models.ParameterDefinition{}, store.ErrNotFound
}

func (s *Store) CreateParameter(ctx context.Context, parameter models.ParameterDefinition) error {
	if err := ctx.Err(); err != nil {
		return err
	}
	if strings.TrimSpace(parameter.Name) == "" {
		return errors.New("jsonfile: parameter name is required")
	}
	s.mu.Lock()
	defer s.mu.Unlock()

	catalog, err := readJSON[parameterFile](s.parametersPath)
	if err != nil {
		return err
	}
	for _, existing := range catalog.Parameters {
		if existing.Name == parameter.Name {
			return fmt.Errorf("jsonfile: parameter %q already exists", parameter.Name)
		}
	}
	catalog.Parameters = append(catalog.Parameters, parameter)
	return writeJSONAtomic(s.parametersPath, catalog)
}

func (s *Store) UpdateParameter(ctx context.Context, parameter models.ParameterDefinition) error {
	if err := ctx.Err(); err != nil {
		return err
	}
	if strings.TrimSpace(parameter.Name) == "" {
		return errors.New("jsonfile: parameter name is required")
	}
	s.mu.Lock()
	defer s.mu.Unlock()

	catalog, err := readJSON[parameterFile](s.parametersPath)
	if err != nil {
		return err
	}
	for i := range catalog.Parameters {
		if catalog.Parameters[i].Name == parameter.Name {
			catalog.Parameters[i] = parameter
			return writeJSONAtomic(s.parametersPath, catalog)
		}
	}
	return store.ErrNotFound
}

func (s *Store) DeleteParameter(ctx context.Context, name string) error {
	if err := ctx.Err(); err != nil {
		return err
	}
	s.mu.Lock()
	defer s.mu.Unlock()

	catalog, err := readJSON[parameterFile](s.parametersPath)
	if err != nil {
		return err
	}
	for i := range catalog.Parameters {
		if catalog.Parameters[i].Name == name {
			catalog.Parameters = append(catalog.Parameters[:i], catalog.Parameters[i+1:]...)
			return writeJSONAtomic(s.parametersPath, catalog)
		}
	}
	return store.ErrNotFound
}

func readJSON[T any](path string) (T, error) {
	var value T
	data, err := os.ReadFile(path)
	if err != nil {
		return value, fmt.Errorf("jsonfile: read %s: %w", path, err)
	}
	if err := json.Unmarshal(data, &value); err != nil {
		return value, fmt.Errorf("jsonfile: decode %s: %w", path, err)
	}
	return value, nil
}

func writeJSONAtomic[T any](path string, value T) error {
	directory := filepath.Dir(path)
	temporary, err := os.CreateTemp(directory, "."+filepath.Base(path)+"-*.tmp")
	if err != nil {
		return fmt.Errorf("jsonfile: create temporary file: %w", err)
	}
	temporaryName := temporary.Name()
	defer os.Remove(temporaryName)

	encoder := json.NewEncoder(temporary)
	encoder.SetIndent("", "  ")
	if err := encoder.Encode(value); err != nil {
		_ = temporary.Close()
		return fmt.Errorf("jsonfile: encode %s: %w", path, err)
	}
	if err := temporary.Sync(); err != nil {
		_ = temporary.Close()
		return fmt.Errorf("jsonfile: sync %s: %w", path, err)
	}
	if err := temporary.Close(); err != nil {
		return fmt.Errorf("jsonfile: close %s: %w", path, err)
	}
	if err := os.Rename(temporaryName, path); err != nil {
		return fmt.Errorf("jsonfile: replace %s: %w", path, err)
	}
	return nil
}
