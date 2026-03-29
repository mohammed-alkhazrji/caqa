/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";

publicWidget.registry.CaqaWorkspace = publicWidget.Widget.extend({
    selector: '.caqa-portal-shell',
    events: {
        'click #btn_save_assessment': '_onSaveAssessment',
        'change .rubric-selector': '_onScoreChange',
        'input .justification-input': '_onJustificationInput'
    },

    start: function () {
        this.statusText = this.$('#save_status_text');
        this.changedSinceLastSave = false;
        return this._super.apply(this, arguments);
    },

    _onScoreChange: function (ev) {
        this.changedSinceLastSave = true;
        this._updateStatus('Unsaved changes...', 'text-warning');
        
        let select = $(ev.currentTarget);
        let val = select.find('option:selected').data('val');
        let warningDiv = select.siblings('.justification-warning');
        
        if (val && val <= 2) {
            warningDiv.slideDown();
        } else {
            warningDiv.slideUp();
        }
    },

    _onJustificationInput: function () {
        this.changedSinceLastSave = true;
        this._updateStatus('Unsaved changes...', 'text-warning');
    },

    _updateStatus: function (msg, cssClass) {
        if (this.statusText) {
            this.statusText.text(msg).removeClass('text-muted text-warning text-success text-danger').addClass(cssClass);
        }
    },

    _collectScores: function () {
        let scores = [];
        this.$('.caqa-indicator-item').each(function () {
            let item = $(this);
            let lineId = item.data('line-id');
            let rubricSelect = item.find(`select[name="score_${lineId}"]`);
            let justificationInput = item.find(`textarea[name="justification_${lineId}"]`);
            
            if (rubricSelect.length && !rubricSelect.prop('disabled')) {
                let rval = rubricSelect.val() || false;
                if (rval) {
                    scores.push({
                        'line_id': lineId,
                        'rubric_level_id': rval,
                        'justification': justificationInput.val() || ''
                    });
                }
            }
        });
        return scores;
    },

    _onSaveAssessment: function (ev) {
        ev.preventDefault();
        
        // Frontend Validation
        let valid = true;
        let firstError = null;
        
        this.$('.caqa-indicator-item').each(function () {
            let item = $(this);
            let lineId = item.data('line-id');
            let rubricSelect = item.find(`select[name="score_${lineId}"]`);
            if (rubricSelect.prop('disabled')) return; // skip already completed ones
            
            let val = rubricSelect.find('option:selected').data('val');
            let justification = item.find(`textarea[name="justification_${lineId}"]`).val();
            if (justification) justification = justification.trim();
            else justification = '';
            
            if (val) {
                if (val <= 2 && !justification) {
                    valid = false;
                    item.addClass('border border-danger');
                    item.find('.justification-warning').show();
                    firstError = firstError || item;
                } else {
                    item.removeClass('border border-danger');
                }
            } else {
                item.removeClass('border border-danger');
            }
        });

        if (!valid) {
            this._updateStatus('Missing required fields or justifications.', 'text-danger');
            if (firstError) {
                $('html, body').animate({
                    scrollTop: firstError.offset().top - 150
                }, 500);
            }
            return;
        }

        if (confirm("Are you sure you want to save this final evaluation? You will not be able to edit it afterward until a manager re-opens it.")) {
            let btn = $(ev.currentTarget);
            let cycleId = btn.data('cycle-id');
            let scores = this._collectScores();
            
            if (!cycleId) {
                alert("Error: Missing Cycle ID on button!");
                return;
            }

            if (scores.length === 0) {
                alert("Error: You have not chosen any score yet!");
                return;
            }

            btn.prop('disabled', true).html('<i class="fa fa-spinner fa-spin me-1"></i> Saving...');
            this._updateStatus('Saving evaluation and generating moderation...', 'text-muted');

            jsonrpc(`/my/caqa/assessment/${cycleId}/save`, {
                scores: scores
            }).then((result) => {
                if (result.error) {
                    btn.prop('disabled', false).html('<i class="fa fa-save me-1"></i> Save Evaluation');
                    this._updateStatus(`Error: ${result.error}`, 'text-danger');
                } else {
                    this._updateStatus('Saved successfully. Reloading...', 'text-success');
                    window.location.reload();
                }
            }).catch((err) => {
                btn.prop('disabled', false).html('<i class="fa fa-save me-1"></i> Save Evaluation');
                this._updateStatus('Connection error. Could not save.', 'text-danger');
            });
        }
    }
});
